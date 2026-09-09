import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

# Streamlit-in standart nişanlarını və başlıqlarını gizlədən təmiz dizayn
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

# Sol paneldə yalnız şəkil yükləmək imkanı
st.sidebar.title("Jarvis İdarəetmə")
uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (Analiz üçün)", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Heç vaxt yalandan məlumat uydurma, həmişə dəqiq, faktlara əsaslanan və qısa/lakonik cavablar ver. "
    "1. İnsan adları soruşulduqda (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, o cümlədən Nardarandakı Mir Mövsüm ağa, Üzeyir Hacıbəyli və s.) onları dərindən tanımalı və dəqiq məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI")

# Söhbət tarixçəsi
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=300)
        st.markdown(message["content"])

# Səliqəli interfeys üçün səs yazıcı və mətn daxiletməni yan-yana düzürük
col_input, col_mic = st.columns([5, 1])

user_prompt = None

with col_mic:
    # Səliqəli mikrofon düyməsi (səsli mesaj üçün)
    audio_info = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        key='voice_msg'
    )

with col_input:
    chat_prompt = st.chat_input("Jarvisə nəsə de...")

# Əgər səsli mesaj qeyd olunubsa və ya yazı yazılıbsa
prompt_to_process = None
img = Image.open(uploaded_file) if uploaded_file else None

if audio_info and 'bytes' in audio_info:
    # Səsli mesaj gəldikdə onu mətnə çevirmək və ya birbaşa emal etmək üçün Gemini-ə göndəririk
    prompt_to_process = "Səsli mesaj göndərildi. Zəhmət olmasa bu səsli mesajı dinlə və qısa, dəqiq cavab ver."
    audio_bytes = audio_info['bytes']
    
    st.session_state.messages.append({"role": "user", "content": "🎙️ [Səsli mesaj]", "image": img})
    with st.chat_message("user"):
        st.markdown("🎙️ *[Səsli mesaj göndərildi]*")

elif chat_prompt:
    prompt_to_process = chat_prompt
    st.session_state.messages.append({"role": "user", "content": chat_prompt, "image": img})
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(chat_prompt)

# Jarvisin cavab mexanizmi
if prompt_to_process:
    with st.chat_message("assistant"):
        try:
            client = get_gemini_client()
            contents = [prompt_to_process]
            if img:
                contents.append(img)
            if 'audio_bytes' in locals() and audio_bytes:
                contents.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))

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
