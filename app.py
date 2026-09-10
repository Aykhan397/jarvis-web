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

# Sol menyu: Parametrlər və Rejimlər
st.sidebar.title("JARVIS v1.0")

st.sidebar.subheader("⚙️ Parametrlər")
# 1. Bütün dilləri seçmək üçün dil seçimi
selected_language = st.sidebar.selectbox("Tətbiqin dili / Dil seçin:", [
    "Azərbaycan", "English", "Türkçe", "Русский", "Español", 
    "Français", "Deutsch", "Italiano", "العربية", "中文", "日本語", "한국어"
])

# 2. Söhbət Keçmişi (Chat History) - Aktiv / Deaktiv etmək üçün parametr
save_history = st.sidebar.checkbox("Söhbət keçmişini yadda saxla", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Rejimlər")

mode_descriptions = {
    "1. Söhbət (Chat)": "ℹ️ Məlumat: Jarvis ilə sərbəst dialoq qurmaq, şəkil yükləmək, video linkləri və konum/ünvanları müzakirə etmək üçündür.",
    "2. Sürətli Sual": "ℹ️ Məlumat: Uzun izahatlar əvəzinə verilən suallara dərhal ən qısa, dəqiq və konkret cavablar vermək üçün nəzərdə tutulub.",
    "3. Kod Köməkçisi": "ℹ️ Məlumat: Proqramlaşdırma dillərində kod yazmaq, səhvləri (bug) tapmaq və kod daxilində şəkil/linkləri analiz etmək üçündür.",
    "4. Strategiya Məsləhətçisi": "ℹ️ Məlumat: Hər hansı plan və ya layihə üçün addım-addım strateji planlar qurur, konum və ya media linklərini qiymətləndirir."
}

menu = st.sidebar.selectbox("Rejimi seç:", list(mode_descriptions.keys()))
st.sidebar.info(mode_descriptions[menu])

system_prompts = {
    "1. Söhbət (Chat)": f"Sən Jarvis-sən, dostcanlı və köməkçi süni intellekt köməkçisisən. İstifadəçinin göndərdiyi şəkilləri təhlil edə, video linklərini şərh edə və konum/ünvan məlumatları üzrə kömək edə bilirsən. Bütün cavablarını mütləq şəkildə '{selected_language}' dilində ver.",
    "2. Sürətli Sual": f"Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və konkret cavablar ver. Şəkil, video linkləri və konum sorğularını nəzərə alaraq qısa cavablandır. Bütün cavablarını '{selected_language}' dilində ver.",
    "3. Kod Köməkçisi": f"Sən peşəkar proqramlaşdırma mütəxəssisisən. Kodları yazır, səhvləri tapırsan. Şəkillərdəki kodları analiz edə, kodlarla bağlı video linkləri və konum/mühit məsələlərini dəstəkləyirsən. İzahları '{selected_language}' dilində ver.",
    "4. Strategiya Məsləhətçisi": f"Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar təqdim edirsən. Şəkilləri, video linklərini və konum məlumatlarını strateji baxımdan qiymətləndirirsən. Cavabları '{selected_language}' dilində ver."
}

st.title("🤖 Jarvis AI Köməkçisi")
st.write(f"Hazırkı rejim: **{menu}** | Seçilmiş dil: **{selected_language}**")

# Şəkil yükləmə paneli
uploaded_file = st.file_uploader("Şəkil yüklə (istəyə bağlı - şəkillə, kodla, konumla və ya video linki ilə bağlı sual verə bilərsən):", type=["jpg", "jpeg", "png"])
image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklənən şəkil", width=300)

# Söhbət keçmişinin idarə edilməsi (Session State)
if menu not in st.session_state:
    st.session_state[menu] = []

# Əgər keçmişi təmizləmək düyməsi əlavə etmək istəsənsə
if st.sidebar.button("🗑️ Söhbət keçmişini təmizlə"):
    st.session_state[menu] = []
    st.rerun()

# Söhbət keçmişini ekranda göstəririk (Səndə olduğu kimi)
for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# İstifadəçidən mesaj qəbulu
if user_input := st.chat_input("Jarvis-ə yaz... (Məsələn: YouTube linki at, konum haqqında soruş və ya şəkil yüklə)"):
    # Əgər parametr aktivdirsə, keçmişə əlavə edirik
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
                
                # Keçmiş mesajları kontekst kimi modelə ötürürük ki, söhbətin ardıcıllığı qorunsun
                history_context = ""
                if save_history and len(st.session_state[menu]) > 1:
                    history_context = "Əvvəlki söhbət tarixçəsi:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state[menu][-6:]])

                full_prompt = f"{system_prompts[menu]}\n\n{history_context}\n\nİstifadəçinin yeni sorğusu: {user_input}"
                contents.append(full_prompt)

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                )
                reply = response.text
            except Exception as e:
                reply = f"Xəta baş verdi: {str(e)}"
            
            st.markdown(reply)
            
            if save_history:
                st.session_state[menu].append({"role": "assistant", "content": reply})
