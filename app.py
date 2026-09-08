import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Jarvis AI", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Açar təyin edilməyib! Lütfən Streamlit ayarlarından əlavə edin.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.6-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Jarvis-ə yaz..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            sys_prompt = f"Sen Jarvis'sin. Kullanıcıya sadık, zeki ve kısa cevaplar ver.\nKullanıcı: {prompt}"
            response = model.generate_content(sys_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
