import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import time
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Həmişə qısa, lakonik, sürətli və dəqiq cavablar ver. Artıq-əskik cümlələr yazma. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və qısa məlumat verməlisən. "
    "2. Hər hansı bir məkan və ya ziyarətgah adı çəkildikdə cavabda mütləq həmin yerin birbaşa kliklənə bilən Google Maps linkini əlavə et: "
    "[Xəritədə bax](https://maps.google.com/?q=yerin_adi). "
    "3. İstifadəçi YouTube linki (və ya Shorts) göndərdikdə həmin videonun kanalını, başlığını, məzmununu və əgər varsa içindəki mahnı/musiqi haqqında məlumatı dərhal təhlil et. "
    "4. Sualları gecikdirmədən, dərhal və dəqiq cavablandır."
)

# Sol tərəfdə həmişə görünən söhbət tarixçəsi paneli
with st.sidebar:
    st.title("💬 Söhbətlər")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        st.session_state.messages = []
        st.session_state.voice_text = ""
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Keçmiş Suallar")
    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "user":
                preview = m["content"][:28] + "..." if len(m["content"]) > 28 else m["content"]
                st.write(f"▫️ {preview}")
    else:
        st.caption("Hələ ki söhbət yoxdur.")

st.title("🤖 Jarvis AI")

uploaded_file = st.file_uploader("Şəkil əlavə et (Analiz üçün)", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

st.markdown("---")

for idx, message in enumerate(st.session_state.messages):
    col_chat, col_action = st.columns([11, 1])
    
    with col_chat:
        with st.chat_message(message["role"]):
            if "image" in message and message["image"]:
                st.image(message["image"], width=300)
            if "audio_bytes" in message and message["audio_bytes"]:
                st.audio(message["audio_bytes"], format="audio/wav")
            st.markdown(message["content"], unsafe_allow_html=True)
            
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

st.write("🎙️ **Səsli mesaj yaz:**")
audio_data = mic_recorder(
    start_prompt="🔴 Başla (Danış)",
    stop_prompt="⏹️ Dayandır",
    just_once=True,
    key='voice_input_btn'
)

if audio_data and 'bytes' in audio_data:
    with st.spinner("Səs mətnə çevrilir..."):
        try:
            client = get_gemini_client()
            audio_bytes = audio_data['bytes']
            
            transcribe_resp = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Bu səsli mesajda nə deyilir? Sadəcə olaraq deyilən sözləri ana dilində yazıya çevir, əlavə heç nə yazma."
                ]
            )
            if transcribe_resp and transcribe_resp.text:
                st.session_state.voice_text = transcribe_resp.text.strip()
                st.success("Səs yazıya çevrildi! Aşağıdakı xanaya düşdü.")
        except Exception as e:
            st.error(f"Səsi oxumaq mümkün olmadı: {e}")

with st.form(key="chat_form", clear_on_submit=True):
    prompt = st.text_input("Jarvisə nəsə de və ya link yapışdır...", value=st.session_state.voice_text, placeholder="Məs: https://youtube.com/... bu videoda nə var?")
    submit_button = st.form_submit_button("➔ Göndər")

if submit_button and prompt:
    st.session_state.voice_text = ""
    img = Image.open(uploaded_file) if uploaded_file else None
    
    st.session_state.messages.append({"role": "user", "content": prompt, "image": img, "audio_bytes": None})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = None
        
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
                    temperature=0.1
                )
            )
            if response and response.text:
                response_text = response.text
            else:
                response_text = "⚠️ Cavab alınmadı, yenidən cəhd edin."

        except Exception as e:
            response_text = f"Xəta baş verdi: {str(e)}"

        if response_text:
            st.markdown(response_text, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
            st.rerun()
