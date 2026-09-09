import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from openai import OpenAI
import anthropic
from PIL import Image

st.set_page_config(page_title="Jarvis AI - Voice Assistant", page_icon="🤖", layout="centered")

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

@st.cache_resource
def get_anthropic_client(api_key):
    return anthropic.Anthropic(api_key=api_key)

if "mode" not in st.session_state:
    st.session_state.mode = "chat"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sol panel
st.sidebar.title("Parametrlər")
model_choice = st.sidebar.selectbox(
    "Model seç:",
    ["Google Gemini (Flash)", "ChatGPT (OpenAI)", "Claude (Anthropic)"]
)

uploaded_file = st.sidebar.file_uploader("Şəkil yüklə", type=["jpg", "jpeg", "png"])

st.sidebar.markdown("---")
if st.sidebar.button("🎙️ Səsli Zəng Rejimi (Live)", use_container_width=True):
    st.session_state.mode = "voice_call"
    st.rerun()

if st.sidebar.button("💬 Yazışma Rejimi", use_container_width=True):
    st.session_state.mode = "chat"
    st.rerun()

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində mükəmməl ünsiyyət quran, sadiq və zəkusan. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

# --- 1. SÖHBƏT (CHAT) REJİMİ ---
if st.session_state.mode == "chat":
    st.title("🤖 Jarvis AI Assistant")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            st.markdown(message["content"])

    if prompt := st.chat_input("Jarvis-ə yaz..."):
        img = Image.open(uploaded_file) if uploaded_file else None
        st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
        
        with st.chat_message("user"):
            if img: st.image(img, width=300)
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response_text = ""
                if model_choice == "Google Gemini (Flash)":
                    client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
                    contents = [prompt, img] if img else [prompt]
                    res = client.models.generate_content(
                        model='gemini-3.6-flash', contents=contents,
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
                elif model_choice == "Claude (Anthropic)":
                    client = get_anthropic_client(st.secrets["ANTHROPIC_API_KEY"])
                    res = client.messages.create(
                        model="claude-3-5-haiku-20241022", max_tokens=1024,
                        system=system_instruction_text, messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = res.content[0].text

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            except Exception as e:
                st.error(f"Xəta: {e}")

# --- 2. SƏSLİ ZƏNG (VOICE CALL) REJİMİ ---
elif st.session_state.mode == "voice_call":
    st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
            <h2>🎙️ Jarvis Səsli Əlaqə Rejimi</h2>
            <p>Düyməyə basıb danışın, Jarvis səsinizi tanıyacaq və cavab verəcək.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=180)

    if st.button("❌ Səsli Rejimi Bağla", use_container_width=True):
        st.session_state.mode = "chat"
        st.rerun()

    # Saf və təmiz JavaScript kod 블oku (Xəta verməyən struktur)
    voice_html = """
    <div style="text-align: center; margin-top: 20px;">
        <button id="start-btn" style="background-color: #ff4b4b; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 30px; cursor: pointer; font-weight: bold;">🎙️ Danışmağa Başla</button>
        <p id="status" style="margin-top: 15px; font-size: 16px; color: #555;">Düyməyə basıb danışın...</p>
        <p id="transcript" style="font-weight: bold; color: #333; margin-top: 10px;"></p>
    </div>

    <script>
        const startBtn = document.getElementById('start-btn');
        const statusEl = document.getElementById('status');
        const transcriptEl = document.getElementById('transcript');

        let recognition;
        if ('webkitSpeechRecognition' in window || 'speechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'az-AZ';
            recognition.interimResults = false;

            startBtn.onclick = function() {
                recognition.start();
                statusEl.innerText = "Dinləyirəm... Danışın.";
                transcriptEl.innerText = "";
            };

            recognition.onresult = function(event) {
                const text = event.results[0][0].transcript;
                transcriptEl.innerText = "Siz dediniz: " + text;
                statusEl.innerText = "Jarvis cavab hazırlayır...";
                
                // Sadə cavab simulyasiyası və səsli oxutma
                let reply = "Eşitdim: " + text;
                if (text.toLowerCase().includes("2 üstə gəl 2") || text.toLowerCase().includes("2 + 2")) {
                    reply = "2 üstə gəl 2, 4 edir.";
                }
                
                speak(reply);
            };

            recognition.onerror = function(event) {
                statusEl.innerText = "Səs tanınmadı. Yenidən cəhd edin.";
            };
        } else {
            statusEl.innerText = "Brauzeriniz səs tanımasını dəstəkləmir. Chrome istifadə edin.";
        }

        function speak(text) {
            var msg = new SpeechSynthesisUtterance(text);
            msg.lang = 'az-AZ';
            window.speechSynthesis.speak(msg);
            statusEl.innerText = "Jarvis: " + text;
        }
    </script>
    """
    components.html(voice_html, height=250)
