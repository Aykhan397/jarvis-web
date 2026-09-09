import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# Səhifənin dizaynı və sağ aşağıdakı nişanları gizlədən CSS
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

# Sol paneldə yalnız şəkil yükləmək üçün imkan saxlayırıq
st.sidebar.title("Jarvis İdarəetmə")
uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (Analiz üçün)", type=["jpg", "jpeg", "png"])

# Jarvis şəxsiyyəti və dəqiqlik təlimatı
system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Heç vaxt yalandan məlumat uydurma, həmişə dəqiq, faktlara əsaslanan və qısa/lakonik cavablar ver. "
    "1. İnsan adları soruşulduqda (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, o cümlədən Nardarandakı Mir Mövsüm ağa, Üzeyir Hacıbəyli və s.) onları dərindən tanımalı və dəqiq məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI")

# Əvvəlki söhbətləri göstər
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=300)
        st.markdown(message["content"])

# Sürətli və dəqiq cavab verən daxiletmə sahəsi
if prompt := st.chat_input("Jarvisə nəsə de və ya sual ver..."):
    img = Image.open(uploaded_file) if uploaded_file else None
    
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            client = get_gemini_client()
            
            # Şəkil varsa və ya yoxdursa məzmuna uyğun tənzimləyirik
            contents = [prompt]
            if img:
                contents.append(img)

            # Dəqiq və sürətli cavab üçün temperature=0.2 (uydurmanın qarşısını alır)
            response = client.models.generate_content(
                model='gemini-3.6-flash', 
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction_text,
                    temperature=0.2
                )
            )
            response_text = response.text
            
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            
        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
