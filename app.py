import streamlit as st
from google import genai
from PIL import Image

# Səhifənin tənzimləmələri
st.set_page_config(page_title="Jarvis - AI İdarəetmə Paneli", page_icon="🤖", layout="wide")

# Təhlükəsizlik üçün API açarını Streamlit Secrets-dən oxuyuruq
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
    "1. Söhbət (Chat)": "Sən Jarvis-sən, dostcanlı və köməkçi süni intellekt köməkçisisən. İstifadəçinin göndərdiyi şəkilləri təhlil edə, video linklərini şərh edə və konum/ünvan məlumatları üzrə kömək edə bilirsən. Azərbaycan dilində cavab ver.",
    "2. Sürətli Sual": "Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və konkret cavablar ver. Şəkil, video linkləri və konum sorğularını nəzərə alaraq qısa cavablandır. Azərbaycan dilində cavab ver.",
    "3. Kod Köməkçisi": "Sən peşəkar proqramlaşdırma mütəxəssisisən. Kodları yazır, səhvləri tapırsan. Şəkillərdəki kodları analiz edə, kodlarla bağlı video linkləri və konum/mühit məsələlərini dəstəkləyirsən.",
    "4. Strategiya Məsləhətçisi": "Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar təqdim edirsən. Şəkilləri, video linklərini və konum məlumatlarını strateji baxımdan qiymətləndirirsən."
}

st.title("🤖 Jarvis AI Köməkçisi")
st.write(f"Hazırkı rejim: **{menu}**")

# Hər 4 rejimdə şəkil yükləmək və konum/link sorğuları üçün ümumi panel
uploaded_file = st.file_uploader("Bir şəkil yüklə (istəyə bağlı - şəkillə, kodla və ya konumla bağlı sual verə bilərsən):", type=["jpg", "jpeg", "png"])
image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklənən şəkil", width=300)

# Hər rejim üçün ayrı söhbət tarixçəsi
if menu not in st.session_state:
    st.session_state[menu] = []

# Əvvəlki mesajları ekrana çap edirik
for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# İstifadəçidən mesaj qəbulu (video linki, konum və ya mətn)
if user_input := st.chat_input("Jarvis-ə yaz... (Məsələn: YouTube linki at, konum haqqında soruş və ya şəkil yüklə)"):
    st.session_state[menu].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        if uploaded_file:
            st.image(uploaded_file, width=150)

    with st.chat_message("assistant"):
        with st.spinner("Jarvis düşünür..."):
            try:
                contents = []
                if image:
                    contents.append(image)
                
                full_prompt = f"{system_prompts[menu]}\n\nİstifadəçi təlimatı / sorğusu (video linki, konum və ya sual): {user_input}"
                contents.append(full_prompt)

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                )
                reply = response.text
            except Exception as e:
                reply = f"Xəta baş verdi: {str(e)}"
            
            st.markdown(reply)
            st.session_state[menu].append({"role": "assistant", "content": reply})
