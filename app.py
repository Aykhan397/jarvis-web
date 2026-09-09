import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Jarvis AI", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Açar təyin edilməyib! Lütfən Streamlit Secrets ayarlarını yoxlayın.")
else:
    client = genai.Client(api_key=api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Jarvis-ə yaz... məsələn: Mirmövsüm ağa kimdir?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Sistem təlimatlarını yeni standartlara uyğun config ilə ötürürük
                system_instruction_text = (
                    "Sən Jarvis-sən. Azərbaycan dilində mükəmməl ünsiyyət quran, sadiq və zəkusan. "
                    "1. İnsan adları (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, məsələn Mirmövsüm ağa) soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
                    "2. İstifadəçi hər hansı bir məkan, yer və ya ziyarətgah soruşduqda, məlumat verməklə yanaşı həmin yerin Google Maps axtarış linkini də cavaba əlavə etməlisən "
                    "(format belə olsun: [Xəritədə bax](https://www.google.com/maps/search/?q=yerin_adi))."
                )

                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction_text,
                    ),
                )
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Xəta detalları: {e}")
