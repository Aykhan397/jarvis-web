import streamlit as st
from google import genai
from PIL import Image

# Səhifənin tənzimləmələri
st.set_page_config(page_title="Jarvis - AI Şəxsi Köməkçi", page_icon="🤖", layout="wide")

# Təhlükəsizlik üçün API açarını Streamlit Secrets-dən oxuyuruq
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Xəta: Streamlit Secrets bölməsində 'GEMINI_API_KEY' tapılmadı! Zəhmət olmasa Secrets ayarlarını yoxlayın.")
    st.stop()

# GenAI müştərisini başladırıq
client = genai.Client(api_key=api_key)

# Sol menyu: Parametrlər və Rejimlər
st.sidebar.title("JARVIS v1.0")

st.sidebar.subheader("⚙️ Parametrlər")
selected_language = st.sidebar.selectbox("Tətbiqin dili / Dil seçin:", [
    "Azərbaycan", "English", "Türkçe", "Русский", "Español", 
    "Français", "Deutsch", "Italiano", "العربية", "中文", "日本語", "한국어"
])

save_history = st.sidebar.checkbox("Söhbət keçmişini yadda saxla", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Rejimlər")

mode_descriptions = {
    "1. Şəxsi Köməkçi (Chat)": "ℹ️ Məlumat: Jarvis ilə sərbəst dialoq qurmaq, şəkil yükləmək, video linkləri və gündəlik sualları müzakirə etmək üçündür.",
    "2. Sürətli Sual": "ℹ️ Məlumat: Uzun izahatlar əvəzinə verilən suallara dərhal ən qısa, dəqiq və konkret cavablar verir.",
    "3. Kod Köməkçisi": "ℹ️ Məlumat: Proqramlaşdırma dillərində kod yazmaq, səhvləri tapmaq və izahat vermək üçündür.",
    "4. Strategiya Məsləhətçisi": "ℹ️ Məlumat: Hər hansı plan və ya layihə üçün addım-addım strateji planlar təqdim edir."
}

menu = st.sidebar.selectbox("Rejimi seç:", list(mode_descriptions.keys()))
st.sidebar.info(mode_descriptions[menu])

system_prompts = {
    "1. Şəxsi Köməkçi (Chat)": f"Sən Jarvis-sən, istifadəçinin şəxsi süni intellekt köməkçisisən. Şəkilləri təhlil edə, video linklərini şərh edə bilirsən. Bütün cavablarını mütləq şəkildə '{selected_language}' dilində ver.",
    "2. Sürətli Sual": f"Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və konkret cavablar ver. Cavabları '{selected_language}' dilində ver.",
    "3. Kod Köməkçisi": f"Sən peşəkar proqramlaşdırma mütəxəssisisən. Kodları yazır, səhvləri tapırsan. İzahları '{selected_language}' dilində ver.",
    "4. Strategiya Məsləhətçisi": f"Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar təqdim edirsən. Cavabları '{selected_language}' dilində ver."
}

st.title("🤖 Jarvis Şəxsi Köməkçi")
st.write(f"Hazırkı rejim: **{menu}** | Seçilmiş dil: **{selected_language}**")

uploaded_file = st.file_uploader("Şəkil yüklə (istəyə bağlı):", type=["jpg", "jpeg", "png"])
image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklənən şəkil", width=300)

if menu not in st.session_state:
    st.session_state[menu] = []

if st.sidebar.button("🗑️ Söhbət keçmişini təmizlə"):
    st.session_state[menu] = []
    st.rerun()

for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Jarvis-ə bir şey yaz..."):
    if save_history:
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
                
                history_context = ""
                if save_history and len(st.session_state[menu]) > 1:
                    history_context = "Əvvəlki söhbət tarixçəsi:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state[menu][-6:]])

                full_prompt = f"{system_prompts[menu]}\n\n{history_context}\n\nİstifadəçinin yeni sorğusu: {user_input}"
                contents.append(full_prompt)

                # Axtarış aləti (google_search) çıxarıldı ki, 429 limiti verməsin
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=contents,
                )
                reply = response.text
            except Exception as e:
                reply = f"Xəta baş verdi: {str(e)}"
            
            st.markdown(reply)
            
            if save_history:
                st.session_state[menu].append({"role": "assistant", "content": reply})
