import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types
from openai import OpenAI
import anthropic
from PIL import Image

st.set_page_config(page_title="Jarvis AI - Voice Talk", page_icon="🤖")
st.title("🤖 Jarvis AI Assistant")

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

@st.cache_resource
def get_anthropic_client(api_key):
    return anthropic.Anthropic(api_key=api_key)

# Sol paneldən model seçimi və səsli oxutma açarı
st.sidebar.title("Parametrlər")
model_choice = st.sidebar.selectbox(
    "Süni intellekt modelini seç:",
    ["Google Gemini (Flash)", "ChatGPT (OpenAI)", "Claude (Anthropic)"]
)

# Cavabların səslə oxunmasını istəyib-istəmədiyini tənzimləmək üçün
speak_response = st.sidebar.checkbox("Səslə cavab vermək (Text-to-Speech)", value=True)

uploaded_file = st.sidebar.file_uploader("Şəkil yüklə (İstəyə bağlı)", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində mükəmməl ünsiyyət quran, sadiq və zəkusan. "
    "1. İnsan adları (tarixi, dini, məşhur və ya yerli şəxsiyyətlər, o cümlədən Nardarandakı Mir Mövsüm ağa və Üzeyir Hacıbəyli) soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
    "2. İstifadəçi hər hansı bir məkan, yer və ya ziyarətgah soruşduqda, məlumat verməklə yanaşı həmin yerin Google Maps axtarış linkini də cavaba əlavə etməlisən "
    "(format məhz belə olsun: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message and message["image"]:
            st.image(message["image"], width=300)
        st.markdown(message["content"])

# Brauzerdə mətnin səslə oxunması üçün JavaScript funksiyası
def speak_text(text):
    # Markdown simvollarını və xəritə linklərini səsləndirmə zamanı oxumaması üçün təmizləyirik
    clean_text = text.replace("*", "").replace("#", "").replace("[Xəritədə bax](", "").replace(")", "")
    js_code = f"""
    <script>
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = 'az-AZ';
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

if prompt := st.chat_input("Jarvis-ə yaz və ya klaviaturanın mikrofonu ilə de (məsələn: 2 üstə gəl 2 nə edir?)..."):
    img = None
    if uploaded_file is not None:
        img = Image.open(uploaded_file)

    st.session_state.messages.append({"role": "user", "content": prompt, "image": img})
    
    with st.chat_message("user"):
        if img:
            st.image(img, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = ""
        
        try:
            if model_choice == "Google Gemini (Flash)":
                api_key = st.secrets.get("GEMINI_API_KEY")
                if not api_key:
                    st.error("Gemini API açarı tapılmadı!")
                else:
                    client = get_gemini_client(api_key)
                    contents = [prompt]
                    if img:
                        contents.append(img)
                        
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction_text,
                        ),
                    )
                    response_text = response.text

            elif model_choice == "ChatGPT (OpenAI)":
                api_key = st.secrets.get("OPENAI_API_KEY")
                if not api_key:
                    st.error("OpenAI API açarı tapılmadı!")
                else:
                    client = get_openai_client(api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_instruction_text},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    response_text = response.choices[0].message.content

            elif model_choice == "Claude (Anthropic)":
                api_key = st.secrets.get("ANTHROPIC_API_KEY")
                if not api_key:
                    st.error("Anthropic API açarı tapılmadı!")
                else:
                    client = get_anthropic_client(api_key)
                    response = client.messages.create(
                        model="claude-3-5-haiku-20241022",
                        max_tokens=1024,
                        system=system_instruction_text,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response_text = response.content[0].text

            if response_text:
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text, "image": None})
                
                # Əgər sol paneldə səsli oxutma işarəlidirsə, brauzer cavabı səsləndirəcək
                if speak_response:
                    speak_text(response_text)

        except Exception as e:
            st.error(f"Xəta baş verdi: {e}")
