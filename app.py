import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

# Streamlit nişanlarını, footer-i və xarici elementləri gizlədən CSS
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sol panel: Şəkil yükləmə və bütün tarixçəni təmizləmə
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
    "2. Məkan, obyekt və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi)). "
    "3. İstənilən dildə verilən sualları həmin dildə dəqiq cavablandır."
)

st.title("🤖 Jarvis AI")

# Söhbət tarixçəsi və hər mesajın sağ üstündə idarəetmə menyusu (Kopyala / Sil)
for idx, message in enumerate(st.session_state.messages):
    # Mesajın başlıq hissəsində sağ tərəfdə kiçik menyu yaratmaq üçün sütunlar
    col_chat, col_action = st.columns([12, 1])
    
    with col_chat:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            st.markdown(message["content"])
            
    with col_action:
        # Hər mesajın sağ üstündə yerləşən səliqəli açılan menyu (select_box əvəzinə pop-up effektli expander/menu)
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
            # Streamlit-də mətnin kopyalanması üçün qısa məlumat və ya kod bloku göstəririk
            st.code(message["content"], language="text")

# İstifadəçinin mesaj daxiletmə paneli
if prompt := st.chat_input("Jarvisə nəsə de..."):
    img = Image.open(uploaded_file) if uploaded_file else None
    
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        success = False
        
        try:
            client = get_gemini_client()
            contents = [prompt]
            if img:
                contents.append(img)

            time.sleep(0.3)

            # Gemini 3.6 Flash modeli ilə sürətli və dəqiq cavab
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction_text,
                    temperature=0.2
                )
            )
            response_text = response.text
            success = True
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                response_text = "⚠️ **Server məşğuldur (Limit aşıldı):** Zəhmət olmasa bir neçə saniyə gözləyib yenidən yazın."
                success = True
            else:
                response_text = f"Xəta baş verdi: {error_str}"
                success = True

        if success and response_text:
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
