import streamlit as st
from google import genai

# Səhifənin tənzimləmələri
st.set_page_config(page_title="Jarvis - AI İdarəetmə Paneli", page_icon="🤖", layout="wide")

# Təhlükəsizlik üçün API açarını birbaşa Streamlit Secrets-dən oxuyuruq
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Xəta: Streamlit Secrets bölməsində 'GEMINI_API_KEY' tapılmadı! Zəhmət olmasa Secrets ayarlarını yoxlayın.")
    st.stop()

# GenAI müştərisini başladırıq
client = genai.Client(api_key=api_key)

# Sol menyu və rejimlər
st.sidebar.title("JARVIS v1.0")
menu = st.sidebar.selectbox("Rejimi seç:", [
    "1. Söhbət (Chat)", 
    "2. Sürətli Sual", 
    "3. Kod Köməkçisi", 
    "4. Strategiya Məsləhətçisi"
])

system_prompts = {
    "1. Söhbət (Chat)": "Sən Jarvis-sən, dostcanlı və köməkçi süni intellekt köməkçisisən. Azərbaycan dilində cavab ver.",
    "2. Sürətli Sual": "Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və konkret cavablar ver. Azərbaycan dilində cavab ver.",
    "3. Kod Köməkçisi": "Sən peşəkar proqramlaşdırma mütəxəssisisən. Təmiz, səliqəli kodlar və izahatlar yaz.",
    "4. Strategiya Məsləhətçisi": "Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar təqdim et."
}

st.title("🤖 Jarvis AI Köməkçisi")
st.write(f"Hazırkı rejim: **{menu}**")

# Hər rejim üçün ayrı söhbət tarixçəsi (session state) yaradırıq
if menu not in st.session_state:
    st.session_state[menu] = []

# Əvvəlki mesajları ekrana çap edirik
for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# İstifadəçidən mesaj qəbulu
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
