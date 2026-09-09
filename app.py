import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="Jarvis AI - Vision", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (İstəyə bağlı)", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində mükəmməl ünsiyyət quran, sadiq və zəkusan. "
    "1. İnsan adları (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, o cümlədən Nardarandakı Mir Mövsüm ağa və Üzeyir Hacıbəyli) soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
    "2. İstifadəçi hər hansı bir məkan, yer və ya ziyarətgah soruşduqda, məlumat verməklə yanaşı həmin yerin Google Maps axtarış linkini də cavaba əlavə etməlisən "
    "(format məhz belə olsun: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=300)
        st.markdown(message["content"])

if prompt := st.chat_input("Jarvis-ə yaz və ya şəkil ilə sual ver..."):
    img = None
    if uploaded_file is not None:
        img = Image.open(uploaded_file)

    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if not api_key:
                st.error("Gemini API açarı tapılmadı!")
            else:
                client = get_gemini_client(api_key)
                
                contents = [prompt]
                if img:
                    contents.append(img)
                    
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction_text,
                    ),
                )
                response_text = response.text
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})

        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
