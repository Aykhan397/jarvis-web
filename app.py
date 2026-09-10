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

# Səsin təkrar işlənməsinin qarşısını almaq üçün ID
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

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
        st.session_state.last_audio_id = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Səsli Otaq Rejimi")
    voice_mode = st.checkbox("🔊 Jarvis səslə cavab versin", value=True)
    
    st.markdown("---")
    st.markdown("### Keçmiş Suallar")
    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "user":
                preview = m["content"][:28] + "..." if len(m["content"]) > 28 else m["content"]
                st.write(f"▫️ {preview}")
    else:
        st.caption("Hələ ki söhbət yoxdur.")

st.title("🤖 Jarvis AI (Səsli Otaq)")

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

st.markdown("🎙️ **Canlı Səsli Söhbət (Danış və burax, Jarvis dərhal cavab versin):**")
audio_data = mic_recorder(
    start_prompt="🔴 Danışmağa Başla",
    stop_prompt="⏹️ Dayandır və Göndər",
    just_once=True,
    key='voice_room_btn'
)

# Səs gələn kimi avtomatik olaraq Jarvisə göndərir və cavab alırıq
if audio_data and 'bytes' in audio_data:
    audio_bytes = audio_data['bytes']
    audio_id = hash(audio_bytes)
    
    if st.session_state.last_audio_id != audio_id:
        st.session_state.last_audio_id = audio_id
        
        with st.spinner("Jarvis səsini dinləyir və düşünür..."):
            try:
                # 1. Səsi mətnə çeviririk
                transcribe_resp = None
                for attempt in range(3):
                    try:
                        time.sleep(1)
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
                        time.sleep(3)

                if transcribe_resp and transcribe_resp.text:
                    user_prompt = transcribe_resp.text.strip()
                    st.session_state.messages.append({"role": "user", "content": user_prompt, "image": None, "audio_bytes": audio_bytes})
                    
                    # 2. Jarvis-dən cavab alırıq
                    response_text = None
                    for attempt in range(3):
                        try:
                            time.sleep(1)
                            client = get_gemini_client(attempt)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[user_prompt],
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
                            time.sleep(3)

                    if response_text:
                        st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
                        
                        # 3. Səsləndirmə (TTS)
                        if voice_mode:
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
                st.error(f"Limit xətası (429) və ya şəbəkə problemi. 10 saniyə gözləyib yenidən cəhd et.")

# Yazılı ünsiyyət üçün dəstək
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
            response_text = f"Jarvis: 429 xətası alındı. Zəhmət olmasa bir az gözlə."

        if response_text:
            st.markdown(response_text, unsafe_allow_html=True)
            if voice_mode:
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
