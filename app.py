import streamlit as st
from google import genai
from google.genai import types
from openai import OpenAI
import anthropic
from PIL import Image

st.set_page_config(page_title="Jarvis AI - Voice", page_icon="🤖", layout="centered")

@st.cache_resource
def get_gemini_client(api_key):
    return genai.Client(api_key=api_key)

@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(api_key=api_key)

@st.cache_resource
def get_anthropic_client(api_key):
    return anthropic.Anthropic(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sol panel
st.sidebar.title("Parametrlər")
model_choice = st.sidebar.selectbox(
    "Model seç:",
    ["Google Gemini (3.6 Flash)", "ChatGPT (OpenAI)", "Claude (Anthropic)"]
)

uploaded_file = st.sidebar.file_uploader("Şəkil yüklə", type=["jpg", "jpeg", "png"])

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə mükəmməl ünsiyyət quran, sadiq, zəkusan. "
    "Bütün dilləri bilir və həmin dildə cavab verirsən. "
    "1. İnsan adları soruşulduqda onları dərindən tanımalı və ətraflı məlumat verməlisən. "
    "2. Məkan və ya ziyarətgah soruşulduqda həmin yerin Google Maps axtarış linkini əlavə etməlisən "
    "(format: [Xəritədə bax](https://maps.google.com/?q=yerin_adi))."
)

st.title("🤖 Jarvis AI - Səsli və Yazılı Rejim")

st.markdown("""
    <p style='color: gray;'>Aşağıdakı daxili mikrofon düyməsindən istifadə edərək səsinizi qeyd edə bilərsiniz.</p>
""", unsafe_allow_html=True)

# Streamlit daxili səs yazıcısı
audio_file = st.audio_input("🎙️ Danışmaq üçün buraya basın")

if audio_file is not None:
    audio_bytes = audio_file.read()
    try:
        if "Gemini" in model_choice:
            client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    "Bu səsli mesajı dinlə və təlimata uyğun olaraq Azərbaycan dilində cavab ver."
                ],
                config=types.GenerateContentConfig(system_instruction=system_instruction_text)
            )
            response_text = response.text
        else:
            response_text = "Səsli giriş üçün zəhmət olmasa Google Gemini (3.6 Flash) modelini seçin."

        st.session_state.messages.append({"role": "user", "content": "🎤 [Səsli Mesaj göndərildi]"})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Xəta baş verdi (Server 503 və ya əlaqə xətası): {e}")

# Yazılı söhbət paneli
if prompt := st.chat_input("Və ya buraya yazı ilə yaza bilərsən..."):
    try:
        if "Gemini" in model_choice:
            client = get_gemini_client(st.secrets["GEMINI_API_KEY"])
            res = client.models.generate_content(
                model='gemini-3.6-flash', contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction_text)
            )
            response_text = res.text
        elif "ChatGPT" in model_choice:
            client = get_openai_client(st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_instruction_text}, {"role": "user", "content": prompt}]
            )
            response_text = res.choices[0].message.content
        else:
            client = get_anthropic_client(st.secrets["ANTHROPIC_API_KEY"])
            res = client.messages.create(
                model="claude-3-5-haiku-20241022", max_tokens=1024,
                system=system_instruction_text, messages=[{"role": "user", "content": prompt}]
            )
            response_text = res.content[0].text

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    except Exception as e:
        st.error(f"Xəta: {e}")

# Söhbət tarixçəsi
st.markdown("---")
st.subheader("💬 Söhbət Tarixçəsi")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
