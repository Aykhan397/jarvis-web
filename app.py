import streamlit as st
from google import genai
from google.genai import types
import time
import json

st.set_page_config(
    page_title="Jarvis AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client(attempt_index):
    if attempt_index % 2 == 1 and "GEMINI_API_KEY_2" in st.secrets:
        key = st.secrets["GEMINI_API_KEY_2"]
    else:
        key = st.secrets.get(
            "GEMINI_API_KEY_1",
            st.secrets.get("GEMINI_API_KEY")
        )

    return genai.Client(api_key=key)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ============================================================
# JARVIS SYSTEM INSTRUCTION
# ============================================================

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə "
    "mükəmməl ünsiyyət quran, sadiq, son dərəcə zəkusan. "
    "Həmişə qısa, lakonik, sürətli və dəqiq cavablar ver. "
    "Artıq-əskik cümlələr yazma. "

    "1. İnsan adları soruşulduqda onları dərindən tanımalı və "
    "qısa məlumat verməlisən. "

    "2. Hər hansı bir məkan və ya ziyarətgah adı çəkildikdə "
    "cavabda mütləq həmin yerin birbaşa kliklənə bilən Google Maps "
    "linkini əlavə et: "
    "[Xəritədə bax](https://maps.google.com/?q=yerin_adi). "

    "3. İstifadəçi YouTube linki və ya Shorts göndərdikdə həmin "
    "videonun kanalını, başlığını, məzmununu və əgər varsa "
    "içindəki mahnı/musiqi haqqında məlumatı təhlil et. "

    "4. Sualları gecikdirmədən, dərhal və dəqiq cavablandır."
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("💬 Söhbətlər")

    if st.button("➕ Yeni Söhbət", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### Keçmiş Suallar")

    if st.session_state.messages:
        for m in st.session_state.messages:
            if m["role"] == "user":
                preview = (
                    m["content"][:28] + "..."
                    if len(m["content"]) > 28
                    else m["content"]
                )
                st.write(f"▫️ {preview}")
    else:
        st.caption("Hələ ki söhbət yoxdur.")


# ============================================================
# TITLE
# ============================================================

st.title("🤖 Jarvis AI - Səsli Söhbət Otağı")


# ============================================================
# HEY JARVIS WAKE WORD SYSTEM
# ============================================================

st.components.v1.html(
    """
    <div style="
        background:#1e1e1e;
        color:white;
        padding:20px;
        border-radius:12px;
        text-align:center;
        font-family:sans-serif;
        border:2px solid #00ffcc;
    ">

        <h3 style="
            margin-top:0;
            color:#00ffcc;
        ">
            🤖 JARVIS
        </h3>

        <p id="statusText"
           style="
                color:#aaa;
                font-size:15px;
           ">
            🎤 "Hey Jarvis" deyin...
        </p>

        <div id="indicator"
             style="
                width:14px;
                height:14px;
                border-radius:50%;
                background:#ff4b4b;
                margin:10px auto;
                box-shadow:0 0 10px #ff4b4b;
             ">
        </div>

    </div>


    <script>

    const status = document.getElementById("statusText");
    const indicator = document.getElementById("indicator");

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    // ========================================================
    // BROWSER CHECK
    // ========================================================

    if (!SpeechRecognition) {

        status.innerText =
            "❌ Bu brauzer Speech Recognition dəstəkləmir. Chrome istifadə edin.";

        indicator.style.background = "#ff0000";

    } else {


        // ====================================================
        // VARIABLES
        // ====================================================

        let recognition = null;

        let mode = "wake";

        let isRunning = false;

        let restarting = false;


        // ====================================================
        // CREATE RECOGNITION
        // ====================================================

        function createRecognition() {

            const r = new SpeechRecognition();

            r.lang = "az-AZ";

            r.interimResults = false;

            r.continuous = false;

            r.maxAlternatives = 5;


            // ================================================
            // START
            // ================================================

            r.onstart = () => {

                isRunning = true;

                if (mode === "wake") {

                    status.innerText =
                        '👂 "Hey Jarvis" gözlənilir...';

                    indicator.style.background = "#ff4b4b";

                    indicator.style.boxShadow =
                        "0 0 15px #ff4b4b";

                } else {

                    status.innerText =
                        "🎤 Jarvis sizi dinləyir...";

                    indicator.style.background = "#00ffcc";

                    indicator.style.boxShadow =
                        "0 0 20px #00ffcc";
                }
            };


            // ================================================
            // RESULT
            // ================================================

            r.onresult = async (event) => {

                const text =
                    event.results[0][0].transcript
                    .toLowerCase()
                    .trim();


                console.log("Recognized:", text);


                // ============================================
                // WAKE WORD MODE
                // ============================================

                if (mode === "wake") {

                    const wakeWords = [
                        "hey jarvis",
                        "hey, jarvis",
                        "hey jarvis",
                        "hej jarvis",
                        "ey jarvis",
                        "hey cervis",
                        "hey jervis",
                        "jarvis"
                    ];


                    const activated =
                        wakeWords.some(word =>
                            text.includes(word)
                        );


                    if (activated) {

                        mode = "command";


                        status.innerText =
                            "🤖 JARVIS aktivləşdi!";

                        indicator.style.background =
                            "#00ffcc";

                        indicator.style.boxShadow =
                            "0 0 25px #00ffcc";


                        // ====================================
                        // JARVIS SPEAKS
                        // ====================================

                        const reply =
                            new SpeechSynthesisUtterance(
                                "Bəli, sizi dinləyirəm."
                            );

                        reply.lang = "az-AZ";

                        reply.rate = 1.05;

                        reply.onend = () => {

                            setTimeout(() => {

                                startRecognition();

                            }, 300);

                        };

                        window.speechSynthesis.cancel();

                        window.speechSynthesis.speak(reply);


                    } else {

                        // Wake word tapılmadı
                        restartWake();

                    }


                // ============================================
                // COMMAND MODE
                // ============================================

                } else {

                    const userSpeech =
                        event.results[0][0].transcript;

                    status.innerText =
                        "Siz dediniz: " + userSpeech;


                    // ========================================
                    // STREAMLIT INPUT TAP
                    // ========================================

                    const inputField =
                        window.parent.document.querySelector(
                            'input[aria-label*="Jarvisə"]'
                        );


                    if (inputField) {

                        // React/Streamlit input-a mətn göndər
                        const setter =
                            Object.getOwnPropertyDescriptor(
                                HTMLInputElement.prototype,
                                "value"
                            ).set;

                        setter.call(
                            inputField,
                            userSpeech
                        );


                        inputField.dispatchEvent(
                            new Event(
                                "input",
                                {
                                    bubbles: true
                                }
                            )
                        );


                        // ====================================
                        // SUBMIT
                        // ====================================

                        setTimeout(() => {

                            const forms =
                                window.parent.document
                                .querySelectorAll("form");


                            if (forms.length > 0) {

                                const form =
                                    forms[forms.length - 1];


                                const submitBtn =
                                    form.querySelector(
                                        'button[type="submit"]'
                                    );


                                if (submitBtn) {
                                    submitBtn.click();
                                }

                            }

                        }, 500);

                    }


                    // Cavabdan sonra Streamlit yenilənəcək
                    mode = "wake";

                }

            };


            // ================================================
            // ERROR
            // ================================================

            r.onerror = (event) => {

                console.log(
                    "Speech error:",
                    event.error
                );


                isRunning = false;


                if (event.error === "not-allowed") {

                    status.innerText =
                        "❌ Mikrofon icazəsi verilməyib.";

                    indicator.style.background =
                        "#ff0000";

                    return;
                }


                if (mode === "wake") {

                    restartWake();

                }

            };


            // ================================================
            // END
            // ================================================

            r.onend = () => {

                isRunning = false;

                if (mode === "wake") {

                    restartWake();

                }

            };


            return r;
        }


        // ====================================================
        // START RECOGNITION
        // ====================================================

        function startRecognition() {

            if (isRunning) {
                return;
            }


            recognition =
                createRecognition();


            try {

                recognition.start();

            } catch (e) {

                console.log(e);

            }

        }


        // ====================================================
        // RESTART WAKE LISTENER
        // ====================================================

        function restartWake() {

            mode = "wake";

            isRunning = false;

            setTimeout(() => {

                startRecognition();

            }, 500);

        }


        // ====================================================
        // START AUTOMATICALLY
        // ====================================================

        setTimeout(() => {

            startRecognition();

        }, 1000);

    }

    </script>
    """,
    height=190,
)


# ============================================================
# CHAT HISTORY
# ============================================================

st.markdown("---")


for idx, message in enumerate(st.session_state.messages):

    col_chat, col_action = st.columns([11, 1])

    with col_chat:

        with st.chat_message(message["role"]):

            st.markdown(
                message["content"],
                unsafe_allow_html=True
            )


    with col_action:

        action = st.selectbox(
            "⚙️",
            ["Seç", "Sil", "Kopyala"],
            key=f"act_{idx}",
            label_visibility="collapsed"
        )


        if action == "Sil":

            st.session_state.messages.pop(idx)

            st.rerun()


        elif action == "Kopyala":

            st.code(
                message["content"],
                language="text"
            )


# ============================================================
# TEXT INPUT
# ============================================================

with st.form(
    key="chat_form",
    clear_on_submit=True
):

    prompt = st.text_input(
        "Jarvisə nəsə de...",
        placeholder='Məsələn: "Hey Jarvis, Bakıda hava necədir?"'
    )


    submit_button = st.form_submit_button(
        "➔ Göndər"
    )


# ============================================================
# AI PROCESSING
# ============================================================

if submit_button and prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    with st.chat_message("user"):

        st.markdown(prompt)


    with st.chat_message("assistant"):

        response_text = None


        try:

            for attempt in range(3):

                try:

                    time.sleep(1)

                    client =
                        get_gemini_client(attempt)


                    response =
                        client.models.generate_content(

                            model="gemini-3.6-flash",

                            contents=[prompt],

                            config=types.GenerateContentConfig(

                                system_instruction=
                                    system_instruction_text,

                                temperature=0.1
                            )
                        )


                    if response and response.text:

                        response_text =
                            response.text

                        break


                except Exception as err:

                    if attempt == 2:

                        raise err

                    time.sleep(2)


            if not response_text:

                response_text =
                    "⚠️ Cavab alınmadı."


        except Exception as e:

            response_text =
                "Jarvis: 429 xətası alındı. Zəhmət olmasa 10 saniyə gözlə."


        # ====================================================
        # SHOW RESPONSE
        # ====================================================

        if response_text:

            st.markdown(
                response_text,
                unsafe_allow_html=True
            )


            # =================================================
            # TEXT TO SPEECH
            # =================================================

            clean_speech = (
                response_text
                .replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .replace("*", "")
            )


            st.components.v1.html(
                f"""
                <script>

                    const speech =
                        new SpeechSynthesisUtterance();

                    speech.text =
                        {json.dumps(clean_speech)};

                    speech.lang = "az-AZ";

                    speech.rate = 1.05;

                    speech.pitch = 1.0;

                    window.speechSynthesis.cancel();

                    window.speechSynthesis.speak(
                        speech
                    );

                </script>
                """,
                height=0
            )


            # =================================================
            # SAVE MESSAGE
            # =================================================

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": response_text
                }
            )


            st.rerun()
