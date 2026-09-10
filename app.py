import streamlit as st
from google import genai
from google.genai import types
import time
import json

# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Jarvis AI",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client(attempt_index=0):
    if attempt_index % 2 == 1 and "GEMINI_API_KEY_2" in st.secrets:
        key = st.secrets["GEMINI_API_KEY_2"]
    else:
        key = st.secrets.get(
            "GEMINI_API_KEY_1",
            st.secrets.get("GEMINI_API_KEY")
        )

    if not key:
        raise ValueError("GEMINI API key tapılmadı.")

    return genai.Client(api_key=key)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "jarvis_enabled" not in st.session_state:
    st.session_state.jarvis_enabled = False


# ============================================================
# JARVIS PERSONALITY
# ============================================================

system_instruction_text = """
Sən Jarvis-sən.

Azərbaycan dilində və digər dillərdə mükəmməl ünsiyyət qur.
Cavabların qısa, lakonik, sürətli və dəqiq olsun.
Lazımsız uzun izahlardan qaç.

1. İnsan adları soruşulduqda qısa və faydalı məlumat ver.

2. Məkan və ya ziyarətgah adı çəkildikdə həmin yer üçün
Google Maps linki əlavə et.

Format:
[Xəritədə bax](https://maps.google.com/?q=yerin_adi)

3. İstifadəçi YouTube linki və ya Shorts linki göndərdikdə
mümkün olan məlumatları təhlil et.

4. İstifadəçinin sualına birbaşa cavab ver.

5. Səsli istifadə üçün cavabları çox uzun etmə.
"""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💬 Söhbətlər")

    if st.button(
        "➕ Yeni Söhbət",
        use_container_width=True
    ):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.markdown("### Keçmiş Suallar")

    if st.session_state.messages:

        for message in st.session_state.messages:

            if message["role"] == "user":

                preview = message["content"]

                if len(preview) > 28:
                    preview = preview[:28] + "..."

                st.write("▫️ " + preview)

    else:

        st.caption("Hələ ki söhbət yoxdur.")


# ============================================================
# TITLE
# ============================================================

st.title("🤖 Jarvis AI")

st.caption(
    'Wake word: "Hey Jarvis"'
)


# ============================================================
# JARVIS ACTIVATION
# ============================================================

if not st.session_state.jarvis_enabled:

    st.info(
        '🎤 İlk dəfə istifadə edərkən aşağıdakı düyməyə bas '
        'və mikrofon icazəsi ver.'
    )

    if st.button(
        "🤖 JARVIS-i AKTİVLƏŞDİR",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.jarvis_enabled = True
        st.rerun()


# ============================================================
# VOICE SYSTEM
# ============================================================

if st.session_state.jarvis_enabled:

    st.components.v1.html(
        """
        <div style="
            background:#151515;
            color:white;
            padding:22px;
            border-radius:16px;
            text-align:center;
            font-family:Arial,sans-serif;
            border:2px solid #00ffcc;
        ">

            <div style="
                font-size:42px;
                margin-bottom:5px;
            ">
                🤖
            </div>

            <h2 style="
                color:#00ffcc;
                margin:5px;
            ">
                JARVIS
            </h2>

            <p id="jarvisStatus"
               style="
                    color:#aaa;
                    font-size:15px;
                    margin:10px;
               ">
                👂 "Hey Jarvis" gözlənilir...
            </p>

            <div id="circle"
                 style="
                    width:16px;
                    height:16px;
                    border-radius:50%;
                    background:#ff3333;
                    margin:15px auto;
                    box-shadow:0 0 15px #ff3333;
                 ">
            </div>

        </div>


        <script>

        // ====================================================
        // JARVIS VOICE SYSTEM
        // ====================================================

        const status =
            document.getElementById("jarvisStatus");

        const circle =
            document.getElementById("circle");


        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;


        // ====================================================
        // BROWSER SUPPORT
        // ====================================================

        if (!SpeechRecognition) {

            status.innerText =
                "❌ Bu brauzer səs tanımanı dəstəkləmir. Chrome istifadə edin.";

            circle.style.background = "#ff0000";

        } else {

            let recognition = null;

            let listening = false;

            let mode = "wake";

            let restarting = false;


            // =================================================
            // WAKE WORDS
            // =================================================

            const wakeWords = [
                "hey jarvis",
                "hey, jarvis",
                "hey jervis",
                "hey cervis",
                "hey carvis",
                "ey jarvis",
                "jarvis"
            ];


            // =================================================
            // NORMALIZE TEXT
            // =================================================

            function normalize(text) {

                return text
                    .toLowerCase()
                    .trim()
                    .replace(/[.,!?]/g, "");

            }


            // =================================================
            // UPDATE UI
            // =================================================

            function setWakeUI() {

                status.innerText =
                    '👂 "Hey Jarvis" gözlənilir...';

                circle.style.background =
                    "#ff3333";

                circle.style.boxShadow =
                    "0 0 15px #ff3333";

            }


            function setListeningUI() {

                status.innerText =
                    "🎤 Sizi dinləyirəm...";

                circle.style.background =
                    "#00ffcc";

                circle.style.boxShadow =
                    "0 0 25px #00ffcc";

            }


            // =================================================
            // CREATE RECOGNIZER
            // =================================================

            function createRecognizer() {

                const r = new SpeechRecognition();

                r.lang = "az-AZ";

                r.continuous = false;

                r.interimResults = false;

                r.maxAlternatives = 5;


                // =============================================
                // START
                // =============================================

                r.onstart = function() {

                    listening = true;

                    if (mode === "wake") {
                        setWakeUI();
                    } else {
                        setListeningUI();
                    }

                };


                // =============================================
                // RESULT
                // =============================================

                r.onresult = function(event) {

                    listening = false;

                    let text =
                        event.results[0][0].transcript;

                    text = normalize(text);


                    console.log(
                        "JARVIS heard:",
                        text
                    );


                    // =========================================
                    // WAKE MODE
                    // =========================================

                    if (mode === "wake") {

                        let activated = false;


                        for (
                            let i = 0;
                            i < wakeWords.length;
                            i++
                        ) {

                            if (
                                text.includes(
                                    wakeWords[i]
                                )
                            ) {

                                activated = true;
                                break;

                            }

                        }


                        if (activated) {

                            mode = "command";


                            status.innerText =
                                "🤖 JARVIS aktivləşdi!";


                            circle.style.background =
                                "#00ffcc";


                            circle.style.boxShadow =
                                "0 0 30px #00ffcc";


                            // =================================
                            // JARVIS RESPONSE
                            // =================================

                            const answer =
                                new SpeechSynthesisUtterance(
                                    "Bəli, sizi dinləyirəm."
                                );


                            answer.lang = "az-AZ";

                            answer.rate = 1.05;

                            answer.pitch = 1.0;


                            answer.onend = function() {

                                setTimeout(
                                    function() {

                                        startRecognition();

                                    },
                                    300
                                );

                            };


                            window.speechSynthesis.cancel();

                            window.speechSynthesis.speak(
                                answer
                            );


                        } else {

                            restartWake();

                        }


                        return;
                    }


                    // =========================================
                    // COMMAND MODE
                    // =========================================

                    if (mode === "command") {

                        if (!text) {

                            restartWake();

                            return;

                        }


                        status.innerText =
                            "Siz dediniz: " + text;


                        sendToStreamlit(text);


                        mode = "wake";

                    }

                };


                // =============================================
                // ERROR
                // =============================================

                r.onerror = function(event) {

                    console.log(
                        "Recognition error:",
                        event.error
                    );


                    listening = false;


                    if (
                        event.error ===
                        "not-allowed"
                    ) {

                        status.innerText =
                            "❌ Mikrofon icazəsi verilməyib.";

                        circle.style.background =
                            "#ff0000";

                        return;

                    }


                    if (
                        event.error ===
                        "service-not-allowed"
                    ) {

                        status.innerText =
                            "❌ Brauzer səs xidmətinə icazə vermədi.";

                        return;

                    }


                    if (mode === "wake") {

                        restartWake();

                    }

                };


                // =============================================
                // END
                // =============================================

                r.onend = function() {

                    listening = false;


                    if (mode === "wake") {

                        restartWake();

                    }

                };


                return r;

            }


            // =================================================
            // START
            // =================================================

            function startRecognition() {

                if (listening) {
                    return;
                }


                try {

                    recognition =
                        createRecognizer();

                    recognition.start();

                } catch (error) {

                    console.log(
                        "Start error:",
                        error
                    );

                    listening = false;

                }

            }


            // =================================================
            // RESTART
            // =================================================

            function restartWake() {

                if (restarting) {
                    return;
                }


                restarting = true;

                mode = "wake";


                setTimeout(
                    function() {

                        restarting = false;

                        startRecognition();

                    },
                    700
                );

            }


            // =================================================
            // SEND TEXT TO STREAMLIT
            // =================================================

            function sendToStreamlit(text) {

                const input =
                    window.parent.document.querySelector(
                        'input[aria-label="Jarvisə nəsə de..."]'
                    );


                if (!input) {

                    console.log(
                        "Streamlit input tapılmadı."
                    );

                    status.innerText =
                        "⚠️ Mətn sahəsi tapılmadı.";

                    restartWake();

                    return;

                }


                // =============================================
                // SET INPUT VALUE
                // =============================================

                const nativeSetter =
                    Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype,
                        "value"
                    ).set;


                nativeSetter.call(
                    input,
                    text
                );


                input.dispatchEvent(
                    new Event(
                        "input",
                        {
                            bubbles: true
                        }
                    )
                );


                // =============================================
                // SUBMIT
                // =============================================

                setTimeout(
                    function() {

                        const form =
                            input.closest("form");


                        if (form) {

                            const button =
                                form.querySelector(
                                    'button[type="submit"]'
                                );


                            if (button) {

                                button.click();

                            }

                        }

                    },
                    400
                );

            }


            // =================================================
            // START AFTER PAGE LOAD
            // =================================================

            setTimeout(
                function() {

                    startRecognition();

                },
                1000
            );

        }

        </script>
        """,
        height=220
    )


# ============================================================
# CHAT HISTORY
# ============================================================

st.markdown("---")


for idx, message in enumerate(
    st.session_state.messages
):

    col_chat, col_action = st.columns(
        [11, 1]
    )


    with col_chat:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"],
                unsafe_allow_html=True
            )


    with col_action:

        action = st.selectbox(
            "⚙️",
            [
                "Seç",
                "Sil",
                "Kopyala"
            ],
            key=f"act_{idx}",
            label_visibility="collapsed"
        )


        if action == "Sil":

            st.session_state.messages.pop(
                idx
            )

            st.rerun()


        elif action == "Kopyala":

            st.code(
                message["content"],
                language="text"
            )


# ============================================================
# CHAT INPUT
# ============================================================

with st.form(
    key="chat_form",
    clear_on_submit=True
):

    prompt = st.text_input(
        "Jarvisə nəsə de...",
        placeholder="Hey Jarvis deyin..."
    )


    submit_button = st.form_submit_button(
        "➔ Göndər"
    )


# ============================================================
# GEMINI
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


        # ================================================
        # API REQUEST
        # ================================================

        try:

            last_error = None


            for attempt in range(3):

                try:

                    client = get_gemini_client(
                        attempt
                    )


                    response = (
                        client.models.generate_content(
                            model="gemini-3.7-flash",
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=
                                    system_instruction_text,
                                temperature=0.2
                            )
                        )
                    )


                    if response and response.text:

                        response_text = (
                            response.text.strip()
                        )

                        break


                except Exception as error:

                    last_error = error

                    if attempt < 2:

                        time.sleep(2)


            if not response_text:

                response_text = (
                    "⚠️ Jarvis cavab yarada bilmədi."
                )


        except Exception as error:

            response_text = (
                "⚠️ Gemini API ilə əlaqə zamanı xəta baş verdi."
            )


        # ================================================
        # SHOW RESPONSE
        # ================================================

        st.markdown(
            response_text,
            unsafe_allow_html=True
        )


        # ================================================
        # SAVE
        # ================================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text
            }
        )


        # ================================================
        # TEXT TO SPEECH
        # ================================================

        clean_speech = (
            response_text
            .replace("[", "")
            .replace("]", "")
            .replace("*", "")
        )


        st.components.v1.html(
            f"""
            <script>

                const text =
                    {json.dumps(clean_speech)};

                if (
                    window.speechSynthesis &&
                    text
                ) {

                    window.speechSynthesis.cancel();

                    const speech =
                        new SpeechSynthesisUtterance(text);

                    speech.lang = "az-AZ";

                    speech.rate = 1.05;

                    speech.pitch = 1.0;

                    window.speechSynthesis.speak(
                        speech
                    );
                }

            </script>
            """,
            height=1
    )
