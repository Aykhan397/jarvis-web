import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

# Sağ aşağıdakı nişanları və xarici elementləri gizlədən təmiz CSS
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

# Sol paneldə şəkil yükləmək və tarixçəni təmizləmək düyməsi
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

# Söhbət tarixçəsini göstəririk və hər mesajın yanında silmə düyməsi qoyuruq
for idx, message in enumerate(st.session_state.messages):
    col_msg, col_del = st.columns([10, 1])
    
    with col_msg:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            st.markdown(message["content"])
            
    with col_del:
        # Hər mesajı ayrı-ayrılıqda silmək üçün kiçik səbət düyməsi
        if st.button("🗑️", key=f"del_{idx}", help="Bu mesajı sil"):
            # İstifadəçi mesajı və ya ona uyğun cavab silinərkən siyahıdan çıxarılır
            st.session_state.messages.pop(idx)
            st.rerun()

# Səhifənin aşağı hissəsində sürətli chat input
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
            st.rerun()
            
        except Exception as e:
            st.error("Serverlə əlaqə zamanı müvəqqəti xəta baş verdi. Zəhmət olmasa yenidən cəhd edin.")
