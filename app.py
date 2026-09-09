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
        response_text = None
        client = get_gemini_client()
        contents = [prompt]
        if img:
            contents.append(img)

        # 429 xətasına qarşı 3 dəfəyə qədər təkrar cəhd etmə mexanizmi (Retry Logic)
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                # Hər sorğudan əvvəl qısa fasilə
                if attempt > 0:
                    time.sleep(3 * attempt) # Hər dəfə gözləmə müddətini artırırıq
                
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
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    continue # Əgər 429-dursa və limit bitməyibsə, dövrü davam etdirib yenidən yoxlayır
                else:
                    error_msg = str(e)
                    break

        if success and response_text:
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
        else:
            if "429" in locals().get('error_msg', '') or not success:
                st.error("⚠️ **Server məşğuldur (429 Limit Xətası):** Pulsuz API limitinə toxunuldu. Zəhmət olmasa 10-15 saniyə gözləyib yenidən yazın və ya Google AI Studio-da hesabınıza ödənişli (pay-as-you-go) plan əlavə edin.")
            else:
                st.error(f"Xəta baş verdi: {locals().get('error_msg', 'Naməlum xəta')}")
