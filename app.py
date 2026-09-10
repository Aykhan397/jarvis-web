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
# GEMINI
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
# SESSION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_started" not in st.session_state:
    st.session_state.voice_started = False


# ============================================================
# JARVIS INSTRUCTION
# ============================================================

system_instruction_text = (
    "Sən Jarvis-sən. Azərbaycan dilində və istənilən digər dildə "
    "mükəmməl ünsiyyət quran, sadiq və son dərəcə zəkisan. "
    "Həmişə qısa, lakonik, sürətli və dəqiq cavablar ver. "
    "Artıq-əskik cümlələr yazma. "
    "1. İnsan adları soruşulduqda onları tanı və qısa məlumat ver. "
    "2. Məkan və ya ziyarətgah adı çəkildikdə birbaşa Google Maps "
    "linki əlavə et: [Xəritədə bax](https://maps.google.com/?q=yerin_adi). "
    "3. İstifadəçi YouTube və ya Shorts linki göndərdikdə mümkün "
    "olan məlumatları təhlil et. "
    "4. Suallara gecikdirmədən, dəqiq cavab ver."
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
                preview = m["content"]
                if len(preview) > 28:
                    preview += "..."
                st.write("▫️ " + preview)
    else:
        st.caption("Hələ ki söhbət yoxdur.")


# ============================================================
# TITLE
# ============================================================

st.title("🤖 Jarvis AI")
st.caption('Wake word: "Hey Jarvis"')


# ============================================================
# VOICE ACTIVATION
# ============================================================

if not st.session_state.voice_started:
    st.info(
        'İlk dəfə istifadə edərkən "JARVIS-i AKTİVLƏŞDİR" '
        'düyməsinə bir dəfə basın. Bu, Android/Chrome-un '
        'mikrofon icazəsi tələb etməsi üçündür.'
    )

    if st.button(
        "🤖 JARVIS-i AKTİVLƏŞDİR",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.voice_started = True
        st.rerun()


if st.session_state.voice_started:

    st.components.v1.html(
        """
        <div style="
            background:#151515;
            color:white;
            padding:20px;
            border-radius:16px;
            text-align:center;
            font-family:Arial,sans-serif;
            border:2px solid #00ffcc;
        ">
            <div style="font-size:42px;">🤖</div>

            <h2 style="color:#00ffcc;margin:5px;">
                JARVIS
            </h2>

            <p id="jarvisStatus"
               style="color:#aaa;font-size:15px;">
                👂 "Hey Jarvis" gözlənilir...
            </p>

            <div id="jarvisDot"
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
        (function () {

            const status =
                document.getElementById("jarvisStatus");

            const dot =
                document.getElementById("jarvisDot");

            const SpeechRecognition =
                window.SpeechRecognition ||
                window.webkitSpeechRecognition;

            if (!SpeechRecognition) {
                status.innerText =
                    "❌ Chrome səs tanımanı dəstəkləmir.";
                return;
            }

            let recognition = null;
            let listening = false;
            let mode = "wake";
            let restarting = false;

            const wakeWords = [
                "hey jarvis",
                "hey, jarvis",
                "hey jervis",
                "hey cervis",
                "hey carvis",
                "ey jarvis",
                "jarvis"
            ];

            function normalize(text) {
                return text
                    .toLowerCase()
                    .trim()
                    .replace(/[.,!?]/g, "");
            }

            function wakeUI() {
                status.innerText =
                    '👂 "Hey Jarvis" gözlənilir...';

                dot.style.background = "#ff3333";
                dot.style.boxShadow =
                    "0 0 15px #ff3333";
            }

            function commandUI() {
                status.innerText =
                    "🎤 Sizi dinləyirəm...";

                dot.style.background = "#00ffcc";
                dot.style.boxShadow =
                    "0 0 25px #00ffcc";
            }

            function createRecognition() {

                const r = new SpeechRecognition();

                r.lang = "az-AZ";
                r.continuous = false;
                r.interimResults = false;
                r.maxAlternatives = 5;

                r.onstart = function () {
                    listening = true;

                    if (mode === "wake") {
                        wakeUI();
                    } else {
                        commandUI();
                    }
                };

                r.onresult = function (event) {

                    listening = false;

                    const text =
                        normalize(
                            event.results[0][0].transcript
                        );

                    console.log(
                        "JARVIS heard:",
                        text
                    );

                    // -------------------------------
                    // WAKE WORD
                    // -------------------------------

                    if (mode === "wake") {

                        let activated = false;

                        for (const word of wakeWords) {
                            if (text.includes(word)) {
                                activated = true;
                                break;
                            }
                        }

                        if (!activated) {
                            restartWake();
                            return;
                        }

                        mode = "command";

                        status.innerText =
                            "🤖 JARVIS aktivləşdi!";

                        dot.style.background = "#00ffcc";
                        dot.style.boxShadow =
                            "0 0 30px #00ffcc";

                        const answer =
                            new SpeechSynthesisUtterance(
                                "Bəli, sizi dinləyirəm."
                            );

                        answer.lang = "az-AZ";
                        answer.rate = 1.05;
                        answer.pitch = 1.0;

                        answer.onend = function () {
                            setTimeout(
                                startRecognition,
                                300
                            );
                        };

                        window.speechSynthesis.cancel();
                        window.speechSynthesis.speak(answer);

                        return;
                    }

                    // -------------------------------
                    // COMMAND
                    // -------------------------------

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

                r.onerror = function (event) {

                    console.log(
                        "Speech error:",
                        event.error
                    );

                    listening = false;

                    if (event.error === "not-allowed") {
                        status.innerText =
                            "❌ Mikrofon icazəsi verilməyib.";
                        dot.style.background = "#ff0000";
                        return;
                    }

                    if (mode === "wake") {
                        restartWake();
                    }
                };

                r.onend = function () {

                    listening = false;

                    if (mode === "wake") {
                        restartWake();
                    }
                };

                return r;
            }

            function startRecognition() {

                if (listening) {
                    return;
                }

                try {
                    recognition =
                        createRecognition();

                    recognition.start();

                } catch (error) {
                    console.log(
                        "Recognition start error:",
                        error
                    );
                }
            }

            function restartWake() {

                if (restarting) {
                    return;
                }

                restarting = true;
                mode = "wake";

                setTimeout(function () {

                    restarting = false;
                    startRecognition();

                }, 700);
            }

            function sendToStreamlit(text) {

                const input =
                    window.parent.document.querySelector(
                        'input[aria-label="Jarvisə nəsə de..."]'
                    );

                if (!input) {

                    status.innerText =
                        "⚠️ Jarvis mətn sahəsi tapılmadı.";

                    restartWake();
                    return;
                }

                const setter =
                    Object.getOwnPropertyDescriptor(
                        HTMLInputElement.prototype,
                        "value"
                    ).set;

                setter.call(input, text);

                input.dispatchEvent(
                    new Event(
                        "input",
                        { bubbles: true }
                    )
                );

                setTimeout(function () {

                    const form =
                        input.closest("form");

                    if (!form) {
                        restartWake();
                        return;
                    }

                    const button =
                        form.querySelector(
                            'button[type="submit"]'
                        );

                    if (button) {
                        button.click();
                    }

                }, 500);
            }

            // Start listening after the page has loaded.
            // Chrome may require microphone permission first.
            setTimeout(
                startRecognition,
                800
            );

        })();
        </script>
        """,
        height=220
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
        placeholder='Məsələn: "Bakının paytaxt olduğunu de"'
    )

    submit_button = st.form_submit_button(
        "➔ Göndər"
    )


# ============================================================
# GEMINI REQUEST
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

            last_error = None

            for attempt in range(3):

                try:

                    client = get_gemini_client(attempt)

                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=
                                system_instruction_text,
                            temperature=0.1
                        )
                    )

                    if response and response.text:
                        response_text = response.text.strip()
                        break

                except Exception as error:

                    last_error = error

                    if attempt < 2:
                        time.sleep(2)

            if not response_text:
                response_text = "⚠️ Cavab alınmadı."

        except Exception:

            response_text = (
                "⚠️ Gemini API ilə əlaqə zamanı xəta baş verdi."
            )

        st.markdown(
            response_text,
            unsafe_allow_html=True
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text
            }
        )

        # ====================================================
        # TEXT TO SPEECH
        # ====================================================

        clean_speech = (
            response_text
            .replace("[", "")
            .replace("]", "")
            .replace("*", "")
        )

        # IMPORTANT:
        # No Python f-string here.
        # This prevents the previous f-string syntax error.

        speech_json = json.dumps(
            clean_speech,
            ensure_ascii=False
        )

        tts_html = """
        <script>
        (function () {

            const text = %s;

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

                window.speechSynthesis.speak(speech);
            }

        })();
        </script>
        """ % speech_json

        st.components.v1.html(
            tts_html,
            height=1
        )
