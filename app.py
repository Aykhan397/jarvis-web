import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="centered")

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

# Səsli mesajdan gələn mətni yadda saxlamaq üçün state
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Heç vaxt yalandan məlumat uydurma, həmişə dəqiq, faktlara əsaslanan və qısa/lakonik cavablar ver. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və dəqiq məlumat verməlisən. "
    "2. Məkan, obyekt və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini mütləq əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi)). "
    "3. İstənilən dildə verilən sualları həmin dildə dəqiq cavablandır."
)

st.title("🤖 Jarvis AI")

# Yuxarıda idarəetmə paneli (Şəkil və Söhbəti təmizlə)
col_ctrl1, col_ctrl2 = st.columns([2, 1])
with col_ctrl1:
    uploaded_file = st.file_uploader("Şəkil əlavə et (Analiz üçün)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
with col_ctrl2:
    if st.button("🗑️ Söhbəti Təmizlə", use_container_width=True):
        st.session_state.messages = []
        st.session_state.voice_text = ""
        st.rerun()

st.markdown("---")

# Mesaj tarixçəsi
for idx, message in enumerate(st.session_state.messages):
    col_chat, col_action = st.columns([11, 1])
    
    with col_chat:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            if "audio_bytes" in message and message["audio_bytes"]:
                st.audio(message["audio_bytes"], format="audio/wav")
            st.markdown(message["content"])
            
    with col_action:
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
            st.code(message["content"], language="text")

# Səsli qeyd yazmaq üçün mikrofon bloku (Danış düyməsi)
st.write("🎙️ **Səsli mesaj yaz:** (Mikrofona bas, danış, səsin yazıya çevriləcək)")
audio_data = mic_recorder(
    start_prompt="🔴 Başla (Danış)",
    stop_prompt="⏹️ Dayandır",
    just_once=True,
    key='voice_input_btn'
)

# Əgər səs qeydə alındısa, onu mətə çevirmək üçün Gemini-ə göndəririk
if audio_data and 'bytes' in audio_data:
    with st.spinner("Səs mətnə çevrilir..."):
        try:
            client = get_gemini_client()
            audio_bytes = audio_data['bytes']
            
            # Səsi mətnə çevirmək üçün xüsusi sorğu
            transcribe_resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Bu səsli mesajda nə deyilir? Sadəcə olaraq deyilən sözləri ana dilində yazıya çevir, əlavə heç nə yazma."
                ]
            )
            if transcribe_resp and transcribe_resp.text:
                st.session_state.voice_text = transcribe_resp.text.strip()
                st.success(جو "Səs uğurla çevrildi! İndi aşağıdakı göndər oxuna basa bilərsən.")
        except Exception as e:
            st.error(f"Səsi oxumaq mümkün olmadı: {e}")

# Mesaj yazma və ya səsdən gələn mətni göndərmə paneli
prompt = st.chat_input("Jarvisə nəsə de...", value=st.session_state.voice_text)

# Mesaj göndərildikdən sonra səs yaddaşını təmizləyirik
if prompt:
    st.session_state.voice_text = ""
    img = Image.open(uploaded_file) if uploaded_file else None
    
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img, "audio_bytes": None})
    
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

            time.sleep(0.2)
            models_to_try = ['gemini-3.6-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
            
            for model_name in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                            temperature=0.2
                        )
                    )
                    if response and response.text:
                        response_text = response.text
                        success = True
                        break
                except Exception:
                    continue
            
            if not success:
                response_text = "⚠️ Server məşğuldur. Zəhmət olmasa bir neçə saniyə gözləyib yenidən cəhd edin."
                success = True

        except Exception as e:
            response_text = f"Xəta baş verdi: {str(e)}"
            success = True

        if success and response_text:
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
