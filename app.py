import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
from streamlit_mic_recorder import mic_recorder

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

# Sol paneldə şəkil yükləmək imkanı
st.sidebar.title("Jarvis İdarəetmə")
uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (Analiz üçün)", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Heç vaxt yalandan məlumat uydurma, həmişə dəqiq, faktlara əsaslanan və qısa/lakonik cavablar ver. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və dəqiq məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI")

# Söhbət tarixçəsini göstər (səsli mesajlara qulaq asmaq üçün st.audio dəstəyi ilə)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=300)
        
        # Əgər mesaj səsli mesajdırsa, pleyerdə qulaq asmaq olar
        if "audio_bytes" in message and message["audio_bytes"]:
            st.audio(message["audio_bytes"], format="audio/wav")
            
        st.markdown(message["content"])

# Səhifənin aşağı hissəsində chat input və səs düyməsini səliqəli yerləşdiririk
chat_prompt = st.chat_input("Jarvisə nəsə de...")

# Göndərmə oxunun yanında mikrofon düyməsi üçün kiçik sütun strukturu
col1, col2 = st.columns([6, 1])
with col2:
    audio_info = mic_recorder(
        start_prompt="🎙️",
        stop_prompt="⏹️",
        just_once=True,
        key='voice_msg_side'
    )

prompt_to_process = None
audio_bytes = None
img = Image.open(uploaded_file) if uploaded_file else None

if audio_info and 'bytes' in audio_info:
    audio_bytes = audio_info['bytes']
    prompt_to_process = "Səsli mesaj göndərildi. Zəhmət olmasa bu səsi dinlə və Azərbaycan dilində qısa, dəqiq cavab ver."
    
    st.session_state.messages.append({
        "role": "user", 
        "content": "🎙️ [Səsli mesaj]", 
        "image": img, 
        "audio_bytes": audio_bytes
    })
    
    with st.chat_message("user"):
        st.audio(audio_bytes, format="audio/wav")
        st.markdown("🎙️ *[Səsli mesaj]*")

elif chat_prompt:
    prompt_to_process = chat_prompt
    st.session_state.messages.append({
        "role": "user", 
        "content": chat_prompt, 
        "image": img, 
        "audio_bytes": None
    })
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(chat_prompt)

# Jarvisin cavablandırma mexanizmi (503 xətasının qarşısını almaq üçün qoruyucu blokla)
if prompt_to_process:
    with st.chat_message("assistant"):
        try:
            client = get_gemini_client()
            contents = [prompt_to_process]
            if img:
                contents.append(img)
            if audio_bytes:
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
            st.session_state.messages.append({
                "role": "user" if False else "assistant", # sadəcə assistant rolu
                "role": "assistant",
                "content": response_text, 
                "image": None, 
                "audio_bytes": None
            })
            
        except Exception as e:
            st.error(f"Server cavab verərkən gecikdi (503 xətası). Zəhmət olmasa bir daha cəhd edin.")
