import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time
import json

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")

def get_gemini_client(attempt_index):
    if attempt_index % 2 == 1 and "GEMINI_API_KEY_2" in st.secrets:
        key = st.secrets["GEMINI_API_KEY_2"]
    else:
        key = st.secrets.get("GEMINI_API_KEY_1", st.secrets.get("GEMINI_API_KEY"))
    return genai.Client(api_key=key)

if "messages" not in st.session_state:
    st.session_state.messages = []

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

st.title("🤖 Jarvis AI - Səsli Söhbət Otağı")

st.components.v1.html(
    """
    <div style="background: #1e1e1e; color: white; padding: 20px; border-radius: 12px; text-align: center; font-family: sans-serif; border: 2px solid #00ffcc;">
        <h3 style="margin-top:0; color: #00ffcc;">🎙️ Canlı Səsli Rejim</h3>
        <p id="statusText" style="color: #aaa; font-size: 14px;">Mikrofonu aktivləşdirmək üçün düyməyə basın və danışın.</p>
        <button id="voiceBtn" style="background: #ff4b4b; color: white; border: none; padding: 12px 24px; font-size: 16px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s;">🔴 Danışmağa Başla</button>
    </div>
    
    <script>
        const btn = document.getElementById('voiceBtn');
        const status = document.getElementById('statusText');
        let isListening = false;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            status.innerText = "Brauzeriniz səs tanınmasını dəstəkləmir (Chrome istifadə edin).";
            btn.style.display = "none";
        } else {
            const recognition = new SpeechRecognition();
            recognition.lang = 'az-AZ';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            btn.onclick = () => {
                if (!isListening) {
                    try {
                        recognition.start();
                    } catch(e) {}
                } else {
                    recognition.stop();
                }
            };

            recognition.onstart = () => {
                isListening = true;
                btn.style.background = '#00ffcc';
                btn.style.color = '#000';
                btn.innerText = '⏹️ Dinlənilir... (Dayandırmaq üçün tıkla)';
                status.innerText = 'Danışın, Jarvis sizi dinləyir...';
            };

            recognition.onresult = async (event) => {
                const userSpeech = event.results[0][0].transcript;
                status.innerText = "Siz dediniz: " + userSpeech;
                
                const inputField = window.parent.document.querySelector('input[aria-label*="Jarvis"]');
                if (inputField) {
                    inputField.value = userSpeech;
                    inputField.dispatchEvent(new Event('input', { bubbles: true }));
                    
                    setTimeout(() => {
                        const form = window.parent.document.querySelector('form');
                        if (form) {
                            const submitBtn = form.querySelector('button[type="submit"]');
                            if (submitBtn) submitBtn.click();
                        }
                    }, 500);
                }
            };

            recognition.onerror = (event) => {
                status.innerText = "Səs xətası: " + event.error;
                resetBtn();
            };

            recognition.onend = () => {
                resetBtn();
            };

            function resetBtn() {
                isListening = false;
                btn.style.background = '#ff4b4b';
                btn.style.color = 'white';
                btn.innerText = '🔴 Danışmağa Başla';
            }
        }
    </script>
    """,
    height=180,
)

st.markdown("---")

for idx, message in enumerate(st.session_state.messages):
    col_chat, col_action = st.columns([11, 1])
    
    with col_chat:
        with st.chat_message(message["role"]):
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

with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("Jarvisə nəsə de...", placeholder="Səsli danışdıqda avtomatik bura yazılacaq...")
    submit_button = st.form_submit_button("➔ Göndər")

if submit_button and prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        try:
            for attempt in range(3):
                try:
                    time.sleep(1)
                    client = get_gemini_client(attempt)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt],
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
                    time.sleep(2)

            if not response_text:
                response_text = "⚠️ Cavab alınmadı."
        except Exception as e:
            response_text = f"Jarvis: 429 xətası alındı. Zəhmət olmasa 10 saniyə gözlə."

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

            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()
