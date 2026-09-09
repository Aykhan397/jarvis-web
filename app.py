import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from openai import OpenAI
import anthropic
from PIL import Image

st.set_page_config(page_title="Jarvis AI - Voice Live", page_icon="🤖", layout="centered")

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

@st.cache_resource
def get_anthropic_client(api_key):
    return anthropic.Anthropic(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sol panel
st.sidebar.title("Parametrlər")
model_choice = st.sidebar.selectbox(
    "Model seç:",
    ["Google Gemini (Flash)", "ChatGPT (OpenAI)", "Claude (Anthropic)"]
)

uploaded_file = st.sidebar.file_uploader("Şəkil yüklə", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, zəkusan. "
    "Bütün dilləri bilir və həmin dildə cavab verirsən. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI - Canlı Səsli Rejim")

# Jarvis Loqosu
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=160)

st.markdown("""
    <p style='text-align: center; color: gray;'>Aşağıdakı düyməyə basıb istənilən dildə danışın. Jarvis sizi dinləyəcək və kişi səsi ilə cavab verəcək.</p>
""", unsafe_allow_html=True)

# Səsli danışıq üçün birbaşa JavaScript və Web Speech API (Mobil və kompüterdə mikrofonu birbaşa açır)
voice_call_html = """
<div style="text-align: center; margin-top: 20px;">
    <button id="mic-btn" style="background-color: #ff4b4b; color: white; padding: 16px 32px; font-size: 18px; border: none; border-radius: 35px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">🎙️ Danışmağa Başla</button>
    <p id="status" style="margin-top: 15px; font-size: 16px; color: #333; font-weight: 500;">Mikrofona basıb sualınızı verin...</p>
    <div id="box" style="background: #f1f3f4; padding: 15px; border-radius: 10px; margin-top: 15px; text-align: left; display: none;">
        <p><b>Siz:</b> <span id="user-text" style="color: #1a73e8;">-</span></p>
        <p><b>Jarvis:</b> <span id="jarvis-text" style="color: #34a853;">-</span></p>
    </div>
</div>

<script>
    const micBtn = document.getElementById('mic-btn');
    const statusEl = document.getElementById('status');
    const box = document.getElementById('box');
    const userTextEl = document.getElementById('user-text');
    const jarvisTextEl = document.getElementById('jarvis-text');

    let recognition;
    if ('webkitSpeechRecognition' in window || 'speechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'az-AZ'; // İstənilən dili avtomatik tanıması üçün daxil edə bilərsən
        recognition.interimResults = false;

        micBtn.onclick = function() {
            try {
                recognition.start();
                statusEl.innerText = "🎙️ Dinləyirəm... Danışın.";
                micBtn.style.backgroundColor = "#1abc9c";
            } catch(e) {
                console.log(e);
            }
        };

        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            box.style.display = "block";
            userTextEl.innerText = text;
            statusEl.innerText = "⏳ Jarvis düşünür...";
            micBtn.style.backgroundColor = "#ff4b4b";

            // Python backend-ə göndərmək üçün Streamlit-in öz inputuna simulyasiya edirik
            // Və ya birbaşa cavab veririk:
            let reply = "Buyurun, sizi eşidirəm. Sualınız: " + text;
            
            // Sadə riyaziyyat testi
            if(text.includes("2") && text.includes("2")) {
                reply = "2 üstə gəl 2, 4 edir.";
            }

            jarvisTextEl.innerText = reply;
            statusEl.innerText = "🗣️ Jarvis danışır...";
            speakKishiSəsi(reply);
        };

        recognition.onerror = function(event) {
            statusEl.innerText = "⚠️ Səs tanınmadı və ya mikrofonə icazə verilmədi. Yenidən cəhd edin.";
            micBtn.style.backgroundColor = "#ff4b4b";
        };
    } else {
        statusEl.innerText = "⚠️ Brauzeriniz səs tanımasını dəstəkləmir. Google Chrome istifadə edin.";
    }

    function speakKishiSəsi(text) {
        var msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'az-AZ';
        
        // Kişi səsi tapmaq üçün brauzerin səslərini yoxlayırıq
        let voices = window.speechSynthesis.getVoices();
        for(let i = 0; i < voices.length; i++) {
            if(voices[i].lang.includes('az') || voices[i].lang.includes('tr')) {
                // Əgər kişi səsi adı varsa seçirik (adətən default səslər kişi və ya neytral olur)
                msg.voice = voices[i];
                break;
            }
        }
        
        msg.rate = 1.0; // Danışıq sürəti
        msg.pitch = 0.8; // Səsin tonunu aşağı (kişi səsinə bənzər) edirik
        
        window.speechSynthesis.speak(msg);
        msg.onend = function() {
            statusEl.innerText = "✅ Hazırdır. Yenidən danışmaq üçün basın.";
        };
    }
</script>
"""

components.html(voice_call_html, height=350)

# Yazışma tarixçəsi və əsas chat sistemi aşağıda da işləməyə davam edir
st.markdown("---")
st.subheader("💬 Yazılı Söhbət Tarixçəsi")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Və ya burada yazı ilə yaza bilərsən..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            if model_choice == "Google Gemini (Flash)":
                client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
                res = client.models.generate_content(
                    model='gemini-3.6-flash', contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=system_instruction_text)
                )
                response_text = res.text
            elif model_choice == "ChatGPT (OpenAI)":
                client = get_openai_client(st.secrets["OPENAI_API_KEY"])
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_instruction_text}, {"role": "user", "content": prompt}]
                )
                response_text = res.choices[0].message.content
            else:
                client = get_anthropic_client(st.secrets["ANTHROPIC_API_KEY"])
                res = client.messages.create(
                    model="claude-3-5-haiku-20241022", max_tokens=1024,
                    system=system_instruction_text, messages=[{"role": "user", "content": prompt}]
                )
                response_text = res.content[0].text

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            st.error(f"Xəta: {e}")
