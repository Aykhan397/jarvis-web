import streamlit as st
import time

st.set_page_config(page_title="Jarvis AI - Multi-Model", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

# Sol paneldən model seçimi
st.sidebar.title("Model Seçimi")
model_choice = st.sidebar.selectbox(
    "Süni intellekt modelini seç:",
    ["Google Gemini (Flash)", "ChatGPT (OpenAI)", "Claude (Anthropic)"]
)

# Sistem təlimatı (Jarvis personajı və xəritə qaydası)
            system_instruction_text = (
                "Sən Jarvis-sən. Azərbaycan dilində mükəmməl ünsiyyət quran, sadiq və zəkusan. "
                "1. İnsan adları (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, o cümlədən Nardarandakı Mir Mövsüm ağa və Üzeyir Hacıbəyli) soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
                "2. İstifadəçi hər hansı bir məkan, yer və ya ziyarətgah soruşduqda, məlumat verməklə yanaşı həmin yerin Google Maps axtarış linkini də cavaba əlavə etməlisən "
                "(format belə olsun: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
            )


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
        response_text = ""
        
        try:
            # 1. Google Gemini
            if model_choice == "Google Gemini (Flash)":
                from google import genai
                from google.genai import types
                
                api_key = st.secrets.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("Gemini API açarı tapılmadı!")
                else:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                        ),
                    )
                    response_text = response.text

            # 2. ChatGPT (OpenAI)
            elif model_choice == "ChatGPT (OpenAI)":
                from openai import OpenAI
                
                api_key = st.secrets.get("OPENAI_API_KEY")
                if not api_key:
                    st.error("OpenAI API açarı tapılmadı!")
                else:
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_instruction_text},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    response_text = response.choices[0].message.content

            # 3. Claude (Anthropic)
            elif model_choice == "Claude (Anthropic)":
                import anthropic
                
                api_key = st.secrets.get("ANTHROPIC_API_KEY")
                if not api_key:
                    st.error("Anthropic API açarı tapılmadı!")
                else:
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=1024,
                        system=system_instruction_text,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = response.content[0].text

            if response_text:
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
