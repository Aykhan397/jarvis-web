import streamlit as st
from google import genai
from PIL import Image

st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API key not found in secrets!")
    st.stop()

client = genai.Client(api_key=api_key)

translations = {
    "Azərbaycan": {
        "title": "JARVIS v1.0",
        "settings": "⚙️ Parametrlər",
        "lang_select": "Tətbiqin dili:",
        "history_toggle": "Söhbət keçmişini yadda saxla",
        "modes_title": "🎯 Rejimlər",
        "main_title": "🤖 Jarvis Şəxsi Köməkçi",
        "current_mode": "Hazırkı rejim:",
        "selected_lang": "Seçilmiş dil:",
        "uploader": "Şəkil yüklə (istəyə bağlı):",
        "clear_history": "🗑️ Söhbət keçmişini təmizlə",
        "chat_input": "Jarvis-ə yaz...",
        "thinking": "Jarvis düşünür...",
        "error": "Xəta baş verdi: "
    },
    "English": {
        "title": "JARVIS v1.0",
        "settings": "⚙️ Settings",
        "lang_select": "App Language:",
        "history_toggle": "Save chat history",
        "modes_title": "🎯 Modes",
        "main_title": "🤖 Jarvis Personal Assistant",
        "current_mode": "Current mode:",
        "selected_lang": "Selected language:",
        "uploader": "Upload image (optional):",
        "clear_history": "🗑️ Clear chat history",
        "chat_input": "Type to Jarvis...",
        "thinking": "Jarvis is thinking...",
        "error": "An error occurred: "
    },
    "Türkçe": {
        "title": "JARVIS v1.0",
        "settings": "⚙️ Ayarlar",
        "lang_select": "Uygulama Dili:",
        "history_toggle": "Sohbet geçmişini kaydet",
        "modes_title": "🎯 Modlar",
        "main_title": "🤖 Jarvis Kişisel Asistan",
        "current_mode": "Mevcut mod:",
        "selected_lang": "Seçilen dil:",
        "uploader": "Resim yükle (isteğe bağlı):",
        "clear_history": "🗑️ Sohbet geçmişini temizle",
        "chat_input": "Jarvis'e yaz...",
        "thinking": "Jarvis düşünüyor...",
        "error": "Bir hata oluştu: "
    },
    "Русский": {
        "title": "JARVIS v1.0",
        "settings": "⚙️ Настройки",
        "lang_select": "Язык приложения:",
        "history_toggle": "Сохранять историю чата",
        "modes_title": "🎯 Режимы",
        "main_title": "🤖 Персональный помощник Jarvis",
        "current_mode": "Текущий режим:",
        "selected_lang": "Выбранный язык:",
        "uploader": "Загрузить фото (необязательно):",
        "clear_history": "🗑️ Очистить историю чата",
        "chat_input": "Напишите Jarvis...",
        "thinking": "Jarvis думает...",
        "error": "Произошла ошибка: "
    }
}

st.sidebar.title("JARVIS v1.0")
st.sidebar.subheader("⚙️ Parametrlər")

selected_language = st.sidebar.selectbox("Dil / Language:", list(translations.keys()))
t = translations[selected_language]

save_history = st.sidebar.checkbox(t["history_toggle"], value=True)

st.sidebar.markdown("---")
st.sidebar.subheader(t["modes_title"])

mode_descriptions = {
    "1. Chat": "Sərbəst dialoq, şəkil və linklərin analizi.",
    "2. Quick Q&A": "Qısa, dəqiq və konkret cavablar.",
    "3. Code Assistant": "Kod yazmaq və səhvləri tapmaq.",
    "4. Strategy Advisor": "Addım-addım strateji planlar."
}

menu = st.sidebar.selectbox("Rejim / Mode:", list(mode_descriptions.keys()))
st.sidebar.info(mode_descriptions[menu])

system_prompts = {
    "1. Chat": f"You are Jarvis, a helpful AI assistant. Answer strictly in '{selected_language}'.",
    "2. Quick Q&A": f"You are Jarvis. Give very short, precise answers. Answer strictly in '{selected_language}'.",
    "3. Code Assistant": f"You are a professional programmer. Write clean code and explain in '{selected_language}'.",
    "4. Strategy Advisor": f"You are a strategic advisor. Provide step-by-step plans in '{selected_language}'."
}

st.title(t["main_title"])
st.write(f"{t['current_mode']} **{menu}** | {t['selected_lang']} **{selected_language}**")

uploaded_file = st.file_uploader(t["uploader"], type=["jpg", "jpeg", "png"])
image = None
if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", width=300)

if menu not in st.session_state:
    st.session_state[menu] = []

if st.sidebar.button(t["clear_history"]):
    st.session_state[menu] = []
    st.rerun()

# Mesajları göstərərkən hər bot mesajına kopyalama rahatlığı üçün expander və ya mətn blokları əlavə edirik
for i, msg in enumerate(st.session_state[menu]):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Əgər mesaj köməkçidəndirsə, istifadəçi asan kopyalasın deyə balaca köməkçi əlavə edirik
        if msg["role"] == "assistant":
            with st.expander("📋 Mətni kopyala / Copy text"):
                st.code(msg["content"], language="text")

if user_input := st.chat_input(t["chat_input"]):
    if save_history:
        st.session_state[menu].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
        if uploaded_file:
            st.image(uploaded_file, width=150)

    with st.chat_message("assistant"):
        with st.spinner(t["thinking"]):
            try:
                contents = []
                if image:
                    contents.append(image)
                
                history_context = ""
                if save_history and len(st.session_state[menu]) > 1:
                    history_context = "History:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state[menu][-6:]])

                full_prompt = f"{system_prompts[menu]}\n\n{history_context}\n\nUser query: {user_input}"
                contents.append(full_prompt)

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contents,
                )
                reply = response.text
            except Exception as e:
                reply = f"{t['error']} {str(e)}"
            
            st.markdown(reply)
            
            # Bot mesajının altında birbaşa kopyalama bloku çıxması üçün avtomatik əlavə olunur
            with st.expander("📋 Mətni kopyala / Copy text"):
                st.code(reply, language="text")
            
            if save_history:
                st.session_state[menu].append({"role": "assistant", "content": reply})
