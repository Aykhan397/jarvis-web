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
    "Sən Jarvis-sən. Mütləq və həmişə yalnız Azərbaycan dilində cavab verməlisən. "
    "İstifadəçinin suallarına səthi deyil, ətraflı, geniş, səlist və izahlı məlumat ver. "
    "İnsanlar, tarixi şəxsiyyətlər və ya hadisələr soruşulduqda hərtərəfli və faydalı məlumat təqdim et. "
    "1. Məkan soruşulanda [Xəritədə bax](https://maps.google.com/?q=yerin_adi) əlavə et. "
    "2. YouTube linki olanda ətraflı məzmun təhlili yaz."
)

with st.sidebar:
    st.title("💬 Söhbətlər")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    voice_mode = st.checkbox("🔊 Səslə cavab vermək", value=True)
    
    st.markdown("---")
    st.markdown("### Keçmiş Suallar")
    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "user":
                preview = m["content"][:28] + "..." if len(m["content"]) > 28 else m["content"]
                st.write(f"▫️ {preview}")

st.title("🤖 Jarvis AI")

uploaded_file = st.file_uploader("Şəkil əlavə et", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
st.markdown("---")

for idx, message in enumerate(st.session_state.messages):
    col_chat, col_action = st.columns([11, 1])
    with col_chat:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            st.markdown(message["content"], unsafe_allow_html=True)
            
    with col_action:
        action = st.selectbox("⚙️", ["Seç", "Sil", "Kopyala"], key=f"act_{idx}", label_visibility="collapsed")
        if action == "Sil":
            st.session_state.messages.pop(idx)
            st.rerun()
        elif action == "Kopyala":
            st.code(message["content"], language="text")

with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("Jarvisə ətraflı sual ver...", placeholder="Məs: Mirmövsüm ağa kimdir?")
    submit_button = st.form_submit_button("➔ Göndər")

if submit_button and prompt:
    img = Image.open(uploaded_file) if uploaded_file else None
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
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

            for attempt in range(2):
                try:
                    client = get_gemini_client(attempt)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                            temperature=0.7
                        )
                    )
                    if response and response.text:
                        response_text = response.text
                        break
                except Exception:
                    time.sleep(0.5)

            if not response_text:
                response_text = "⚠️ Cavab alınmadı."
        except Exception as e:
            response_text = "Jarvis: Limit aşımı. Bir az gözləyin."

        if response_text:
            st.markdown(response_text, unsafe_allow_html=True)
            
            if voice_mode:
                clean_speech = response_text.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("*", "")
                st.components.v1.html(f"""
                    <script>
                        const speech = new SpeechSynthesisUtterance();
                        speech.text = {json.dumps(clean_speech)};
                        speech.lang = 'az-AZ';
                        speech.rate = 1.0;
                        window.speechSynthesis.speak(speech);
                    </script>
                """, height=0)

            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
