import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

st.sidebar.title("Jarvis İdarəetmə")
uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (Analiz üçün)", type=["jpg", "jpeg", "png"])

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Bütün Söhbəti Təmizlə", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Heç vaxt yalandan məlumat uydurma, həmişə dəqiq, faktlara əsaslanan və qısa/lakonik cavablar ver. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və dəqiq məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI")

for idx, message in enumerate(st.session_state.messages):
    col_msg, col_del = st.columns([10, 1])
    
    with col_msg:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            st.markdown(message["content"])
            
    with col_del:
        if st.button("🗑️", key=f"del_{idx}", help="Bu mesajı sil"):
            st.session_state.messages.pop(idx)
            st.rerun()

if prompt := st.chat_input("Jarvisə nəsə de..."):
    img = Image.open(uploaded_file) if uploaded_file else None
    
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = get_gemini_client()
            contents = [prompt]
            if img:
                contents.append(img)

            # Qısa gecikmə əlavə edirik ki, 429 limitinə düşmə ehtimalı azalsın
            time.sleep(0.5)

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction_text,
                    temperature=0.2
                )
            )
            response_text = response.text
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                st.error("⚠️ **Limit aşıldı (429 Xətası):** Google AI Studio API açarınızın dəqiqəlik sorğu limiti dolub. Zəhmət olmasa Google AI Studio-dan yeni bir API açarı yaradın və `secrets.toml` faylına yazın.")
            else:
                st.error(f"Xəta baş verdi: {e}")
