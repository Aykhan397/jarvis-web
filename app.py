import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time
import json
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")

def get_gemini_client(attempt_index):
    if attempt_index % 2 == 1 and "GEMINI_API_KEY_2" in st.secrets:
        key = st.secrets["GEMINI_API_KEY_2"]
    else:
        key = st.secrets.get("GEMINI_API_KEY_1", st.secrets.get("GEMINI_API_KEY"))
    return genai.Client(api_key=key)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Həmişə qısa, lakonik, sürətli və dəqiq cavablar ver. Artıq-əskik cümlələr yazma. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və qısa məlumat verməlisən. "
    "2. Hər hansı bir məkan və ya ziyarətgah adı çəkildikdə cavabda mütləq həmin yerin birbaşa kliklənə bilən Google Maps linkini əlavə et: "
    "[Xəritədə bax](https://maps.google.com/?q=yerin_adi). "
    "3. İstifadəçi YouTube linki (və ya Shorts) göndərdikdə həmin videonun kanalını, başlığını, məzmununu və əgər varsa içindəki mahnı/musiqi haqqında məlumatı dərhal təhlil et. "
    "4. Sualları gecikdirmədən, dərhal və dəqiq cavablandır."
)

with st.sidebar:
    st.title("💬 Söhbətlər")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        st.session_state.messages = []
        st.session_state.voice_text = ""
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Səsli Söhbət Rejimi")
    # Sənin istədiyin o səsli rejim düyməsi (aktiv olduqda Jarvis həm səslə dinləyir, həm də səslə cavab verir)
    voice_chat_active = st.toggle("🎙️ Səsli Rejim (Canlı Söhbət)", value=True)
    
    st.markdown("---")
    st.markdown("### Keçmiş Suallar")
    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "user":
                preview = m["content"][:28] + "..." if len(m["content"]) > 28 else m["content"]
                st.write(f"▫️ {preview}")
    else:
        st.caption("Hələ ki söhbət yoxdur.")

st.title("🤖 Jarvis AI")

uploaded_file = st.file_uploader("Şəkil əlavə et (Analiz üçün)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

st.markdown("---")

for idx, message in enumerate(st.session_state.messages):
    col_chat, col_action = st.columns([11, 1])
    
    with col_chat:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            if "audio_bytes" in message and message["audio_bytes"]:
                st.audio(message["audio_bytes"], format="audio/wav")
            st.markdown(message["content"], unsafe_allow_html=True)
            
    with col_action:
        action = st.selectbox(
            "⚙️", 
            ["Seç", "Sil", "Kopyala"], 
            key=f"act_{idx}", 
            label_visibility="collapsed"
        )
        
        if action == "Sil":
            st.session_state.messages.pop(idx)
            st.rerun()
        elif action == "Kopyala":
            st.code(message["content"], language="text")

# Səsli söhbət üçün xüsusi mavi/qırmızı idarəetmə düyməsi
if voice_chat_active:
    st.markdown("### 🎙️ Jarvislə Səsli Danışıq Paneli")
    st.info("Aşağıdakı düyməyə basıb danış, buraxdıqda və ya dayandırdıqda Jarvis səni dinləyib səsli cavab verəcək.")
    
    audio_data = mic_recorder(
        start_prompt="🔴 Səsli Söhbətə Başla (Danış)",
        stop_prompt="⏹️ Dayandır və Göndər",
        just_once=True,
        key='live_voice_chat_btn'
    )

    if audio_data and 'bytes' in audio_data:
        with st.spinner("Jarvis səsinə qulaq asır..."):
            try:
                audio_bytes = audio_data['bytes']
                transcribe_resp = None
                
                for attempt in range(3):
                    try:
                        time.sleep(2)
                        client = get_gemini_client(attempt)
                        transcribe_resp = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[
                                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                                "Bu səsli mesajda nə deyilir? Sadəcə olaraq deyilən sözləri ana dilində yazıya çevir, əlavə heç nə yazma."
                            ]
                        )
                        if transcribe_resp and transcribe_resp.text:
                            break
                    except Exception as err:
                        if attempt == 2:
                            raise err
                        time.sleep(4)

                if transcribe_resp and transcribe_resp.text:
                    st.session_state.voice_text = transcribe_resp.text.strip()
                    st.success(f"Eşidildi: {st.session_state.voice_text}")
                    
                    # Səsi avtomatik olaraq söhbətə əlavə edib Jarvisdən cavab alırıq
                    prompt_text = st.session_state.voice_text
                    st.session_state.voice_text = ""
                    
                    st.session_state.messages.append({"role": "user", "content": prompt_text, "image": None, "audio_bytes": audio_bytes})
                    
                    # Jarvis cavabı
                    response_text = None
                    for attempt in range(3):
                        try:
                            time.sleep(2)
                            client = get_gemini_client(attempt)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[prompt_text],
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction_text,
                                    temperature=0.1
                                )
                            )
                            if response and response.text:
                                response_text = response.text
                                break
                        except Exception as err:
                            if attempt == 2:
                                raise err
                            time.sleep(4)

                    if response_text:
                        st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
                        
                        # Jarvis-in səslə cavab verməsi
                        clean_speech = response_text.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("*", "")
                        st.components.v1.html(f"""
                            <script>
                                const speech = new SpeechSynthesisUtterance();
                                speech.text = {json.dumps(clean_speech)};
                                speech.lang = 'az-AZ';
                                speech.rate = 1.05;
                                window.speechSynthesis.speak(speech);
                            </script>
                        """, height=0)
                        
                        st.rerun()

            except Exception as e:
                st.error(f"429 xətası alındı. Zəhmət olmasa 10-15 saniyə gözlə.")

# Əgər mətnlə də yazmaq istəsən, aşağıda söhbət qutusu qalır
with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("Və ya mətn ilə yaz...", placeholder="Məs: Salam Jarvis")
    submit_button = st.form_submit_button("➔ Göndər")

if submit_button and prompt:
    img = Image.open(uploaded_file) if uploaded_file else None
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img, "audio_bytes": None})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        try:
            contents = [prompt]
            if img:
                contents.append(img)

            for attempt in range(3):
                try:
                    time.sleep(2)
                    client = get_gemini_client(attempt)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                            temperature=0.1
                        )
                    )
                    if response and response.text:
                        response_text = response.text
                        break
                except Exception as err:
                    if attempt == 2:
                        raise err
                    time.sleep(4)

            if not response_text:
                response_text = "⚠️ Cavab alınmadı."
        except Exception as e:
            response_text = f"Jarvis: 429 xətası. Zəhmət olmasa bir az gözlə."

        if response_text:
            st.markdown(response_text, unsafe_allow_html=True)
            clean_speech = response_text.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("*", "")
            st.components.v1.html(f"""
                <script>
                    const speech = new SpeechSynthesisUtterance();
                    speech.text = {json.dumps(clean_speech)};
                    speech.lang = 'az-AZ';
                    speech.rate = 1.05;
                    window.speechSynthesis.speak(speech);
                </script>
            """, height=0)

            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
