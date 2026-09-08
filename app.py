import streamlit as st
from google import genai

st.set_page_config(page_title="Jarvis AI", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Açar təyin edilməyib! Lütfən Streamlit Secrets ayarlarını yoxlayın.")
else:
    # Google-un yeni rəsmi SDK müştərisi
    client = genai.Client(api_key=api_key)

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
            try:
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=f"Sen Jarvis'sin. Kullanıcıya sadık, zeki ve kısa cevaplar ver.\nKullanıcı: {prompt}"
                )
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                # Dəqiq xəta mesajını ekrana çıxarırıq ki, səbəbini görək
                st.error(f"Xəta detalları: {e}")
