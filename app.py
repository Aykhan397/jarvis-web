import streamlit as st
from google import genai

# Sehifenin tenzimlemeleri
st.set_page_config(page_title="Jarvis - AI Idareetme Paneli", page_icon="🤖", layout="wide")

# API açari
api_key = st.secrets.get("GEMINI_API_KEY") or "SENIN_GEMINI_API_ACARIN"

client = genai.Client(api_key=api_key)

st.sidebar.title("JARVIS v1.0")
menu = st.sidebar.selectbox("Rejimi sec:", [
    "1. Sohbet (Chat)", 
    "2. Suretli Sual", 
    "3. Kod Komekcisi", 
    "4. Strategiya Meslehetcisi"
])

system_prompts = {
    "1. Sohbet (Chat)": "Sen Jarvis-sen, dostcanli ve komekci suni intellekt komekcisisen. Azerbaycan dilinde cavab ver.",
    "2. Suretli Sual": "Sen Jarvis-sen. Verilen suallara cox qisa, deqiq ve konkret cavablar ver. Azerbaycan dilinde cavab ver.",
    "3. Kod Komekcisi": "Sen pesekar proqramlasdirma mutexessisisen. Temiz, seliqeli kodlar ve izahatlar yaz.",
    "4. Strategiya Meslehetcisi": "Sen strateji planlasma ve meslehetci Jarvis-sen. Istifadeciye addim-addim planlar teqdim et."
}

st.title("🤖 Jarvis AI Komekcisi")
st.write(f"Hazirki rejim: **{menu}**")

# Sohbet tarixcesini saxlamaq ucun
if menu not in st.session_state:
    st.session_state[menu] = []

# Evvelki mesajlari goster
for msg in st.session_state[menu]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Istifadeciden input almaq
if user_input := st.chat_input("Jarvis-e bir sey yaz..."):
    st.session_state[menu].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Jarvis dusunur..."):
            try:
                prompt = f"{system_prompts[menu]}\n\nIstifadeci: {user_input}"
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                reply = response.text
            except Exception as e:
                reply = f"Xeta bas verdi: {str(e)}"
            
            st.markdown(reply)
            st.session_state[menu].append({"role": "assistant", "content": reply})
