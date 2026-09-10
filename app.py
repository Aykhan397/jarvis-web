import streamlit as st
from google import genai

# Səhifənin tənzimləmələri
st.set_page_config(page_title="Jarvis - AI İdarəetmə Paneli", page_icon="🤖", layout="wide")

# API açarı (öz açarını bura yaz və ya Streamlit secrets istifadə et)
api_key = st.secrets.get("GEMINI_API_KEY") or "SƏNİN_GEMİNİ_APİ_AÇARIN"

client = genai.Client(api_key=api_key)

st.sidebar.title("JARVIS v1.0")
menu = st.sidebar.selectbox("Rejimi seç:", [
    "1. Söhbət (Chat)", 
    "2. Sürətli Sual", 
    "3. Kod Köməkçisi", 
    "4. Strategiya Məsləhətçisi"
])

system_prompts = {
    "1. Söhbət (Chat)": "Sən Jarvis-sən, dostcanlı və köməkçi süni intellekt köməkçisisən.",
    "2. Sürətli Sual": "Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və laktik cavablar ver.",
    "3. Kod Köməkçisi": "Sən peşəkar proqramlaşdırma mütəxəssisi Jarvis-sən. Təmiz, səliqəli kodlar və izahatlar yaz.",
    "4. Strategiya Məsləhətçisi": "Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar və məsləhətlər təqdim et."
}

st.title("🤖 Jarvis AI Köməkçisi")
st.write(f"Hazırkı rejim: **{menu}**")

# Söhbət tarixçəsini saxlamaq üçün
if menu not in st.session_state:
    st.session_state[menu] = []

# Əvvəlki mesajları göstər
for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# İstifadəçidən input almaq
if user_input := st.chat_input("Jarvis-ə bir şey yaz..."):
    st.session_state[menu].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Jarvis düşünür..."):
            try:
                prompt = f"{system_prompts[menu]}\n\nİstifadəçi: {user_input}"
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                reply = response.text
            except Exception as e:
                reply = f"Xəta baş verdi: {str(e)}"
            
            st.markdown(reply)
            st.session_state[menu].append({"role": "assistant", "content": reply})
