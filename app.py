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

if "room_active" not in st.session_state:
    st.session_state.room_active = False

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
    st.markdown("### 🎙️ Discord Səsli Otaq")
    
    # Canlı səsli otağı açan və ya bağlayan düymələr
    if not st.session_state.room_active:
        if st.button("🟢 Səsli Otağa Qoşul", use_container_width=True, type="primary"):
            st.session_state.room_active = True
            st.rerun()
    else:
        if st.button("🔴 Otaqdan Çıx", use_container_width=True):
            st.session_state.room_active = False
            st.rerun()

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

# Əgər səsli otaq aktivdirsə, ekranın ortasında Discord tipli səsli otaq paneli görünür
if st.session_state.room_active:
    st.markdown("---")
    st.markdown("### 🎧 Canlı Səsli Söhbət Otağı Aktivdir")
    st.info("İndi mikrofon səni dinləyir. Danışdıqdan sonra Jarvis avtomatik səsli cavab verəcək.")
    
    st.components.v1.html("""
        <div style="background: #121212; color: #00ffcc; padding: 30px; border-radius: 16px; text-align: center; font-family: sans-serif; border: 2px solid #00ffcc;">
            <h2>🎙️ Jarvis Səsli Otaq Qoşuldu</h2>
            <p id="roomStatus" style="color: #fff; font-size: 18px; margin: 20px 0;">Dinlənilir... Danışmağa başlayın.</p>
            <button id="toggleRoom" style="background: #ff4b4b; color: white; border: none; padding: 12px 28px; font-size: 16px; border-radius: 8px; cursor: pointer; font-weight: bold;">Mikrofonu Bağla</button>
        </div>
        <script>
            const statusText = document.getElementById('roomStatus');
            const toggleBtn = document.getElementById('toggleRoom');
            let listening = true;

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.lang = 'az-AZ';
                recognition.continuous = true;
                recognition.interimResults = false;

                recognition.onresult = (event) => {
                    const speechToText = event.results[event.results.length - 1][0].transcript;
                    statusText.innerText = "Siz dediniz: " + speechToText;
                    
                    // Jarvis cavab simulyasiyası və səsləndirmə
                    const utterance = new SpeechSynthesisUtterance("Eşitdim sizi, buyurun.");
                    utterance.lang = 'az-AZ';
                    window.speechSynthesis.speak(utterance);
                };

                recognition.onerror = (event) => {
                    statusText.innerText = "Səs xətası: " + event.error;
                };

                recognition.onend = () => {
                    if (listening) {
                        try { recognition.start(); } catch(e) {}
                    }
                };

                recognition.start();

                toggleBtn.onclick = () => {
                    listening = !listening;
                    if (listening) {
                        recognition.start();
                        toggleBtn.style.background = '#ff4b4b';
                        toggleBtn.innerText = 'Mikrofonu Bağla';
                        statusText.innerText = 'Dinlənilir...';
                    } else {
                        recognition.stop();
                        toggleBtn.style.background = '#4CAF50';
                        toggleBtn.innerText = 'Mikrofonu Aç';
                        statusText.innerText = 'Mikrofon söndürüldü.';
                    }
                };
            } else {
                statusText.innerText = "Brauzeriniz səs tanımasını dəstəkləmir.";
            }
        </script>
    """, height=250)
    st.markdown("---")

else:
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

    st.write("🎙️ **Səsli mesaj yaz:**")
    audio_data = mic_recorder(
        start_prompt="🔴 Başla (Danış)",
        stop_prompt="⏹️ Dayandır",
        just_once=True,
        key='voice_input_btn'
    )

    if audio_data and 'bytes' in audio_data:
        with st.spinner("Səs mətnə çevrilir..."):
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
                    st.success("Səs yazıya çevrildi!")
                    st.rerun()
            except Exception as e:
                st.error(f"Hər iki açar limitə düşdü (429). 10-15 saniyə gözləyib yenidən cəhd et.")

    with st.form(key="chat_form", clear_on_submit=True):
        prompt = st.text_input("Jarvisə nəsə de və ya link yapışdır...", value=st.session_state.voice_text, placeholder="Məs: https://youtube.com/... bu videoda nə var?")
        submit_button = st.form_submit_button("➔ Göndər")

    if submit_button and prompt:
        st.session_state.voice_text = ""
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
                    response_text = "⚠️ Cavab alınmadı, limit dolmuş ola bilər."

            except Exception as e:
                response_text = f"Jarvis: 429 xətası alındı. Hər iki açar limitə çatıb, zəhmət olmasa 10-15 saniyə gözlə."

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
