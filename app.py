import streamlit as st
from google import genai
from google.genai import types
import time
import json
import re

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

system_instruction_text = """
Sən Jarvis-sən.

İstifadəçi ilə Azərbaycan dilində əsasən qısa, ağıllı və təbii
şəkildə danış.

Özünü robot kimi yox, şəxsi köməkçi kimi apar.

Cavabları mümkün qədər qısa və konkret ver.

İstifadəçi sənə sual verdikdə birbaşa cavab ver.
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
        'Jarvis-i aktivləşdirmək üçün aşağıdakı düyməyə basın.'
    )

    if st.button(
        "🤖 JARVIS-i AKTİVLƏŞDİR",
        use_container_width=True,
        type="primary"
    ):

        st.session_state.voice_started = True
        st.rerun()


# ============================================================
# VOICE SYSTEM
# ============================================================

if st.session_state.voice_started:

    st.components.v1.html(
        """
<!DOCTYPE html>

<html>

<head>

<style>

.jarvis-box {

    background:
        linear-gradient(
            145deg,
            #101010,
            #181818
        );

    color:white;

    padding:25px;

    border-radius:20px;

    text-align:center;

    font-family:Arial;

    border:2px solid #00ffcc;

    box-shadow:
        0 0 25px rgba(0,255,204,.15);

}

.jarvis-logo {

    font-size:50px;

}

.jarvis-title {

    color:#00ffcc;

    font-size:28px;

    font-weight:bold;

    margin-top:5px;

}

#jarvisStatus {

    color:#aaa;

    font-size:16px;

}

#jarvisDot {

    width:18px;

    height:18px;

    border-radius:50%;

    background:#ff3333;

    margin:18px auto;

    box-shadow:
        0 0 18px #ff3333;

}

</style>

</head>


<body>

<div class="jarvis-box">

    <div class="jarvis-logo">
        🤖
    </div>

    <div class="jarvis-title">
        JARVIS
    </div>

    <p id="jarvisStatus">
        👂 "Hey Jarvis" gözlənilir...
    </p>

    <div id="jarvisDot"></div>

</div>


<script>

(function () {

    // ========================================================
    // ELEMENTS
    // ========================================================

    const status =
        document.getElementById(
            "jarvisStatus"
        );

    const dot =
        document.getElementById(
            "jarvisDot"
        );


    // ========================================================
    // SPEECH RECOGNITION
    // ========================================================

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


    // ========================================================
    // WAKE WORDS
    // ========================================================

    const wakeWords = [

        "hey jarvis",
        "hey, jarvis",
        "hey jervis",
        "hey cervis",
        "hey carvis",
        "ey jarvis",
        "jarvis"

    ];


    // ========================================================
    // NORMALIZE
    // ========================================================

    function normalize(text) {

        return text
            .toLowerCase()
            .trim()
            .replace(/[.,!?]/g, "");

    }


    // ========================================================
    // JARVIS VOICE
    // ========================================================

    function speakJarvis(
        text,
        callback
    ) {

        if (!window.speechSynthesis) {

            if (callback)
                callback();

            return;
        }


        window.speechSynthesis.cancel();


        const speech =
            new SpeechSynthesisUtterance(
                text
            );


        // Azərbaycan dili

        speech.lang = "az-AZ";


        // ====================================================
        // KİŞİ SƏSİNİ TAP
        // ====================================================

        const voices =
            window.speechSynthesis
                .getVoices();


        let maleVoice = null;


        const maleNames = [

            "Microsoft David",
            "Microsoft Mark",
            "Google UK English Male",
            "Google US English Male",
            "Daniel",
            "Alex",
            "Thomas",
            "Arthur",
            "Fred",
            "Male"

        ];


        // Əvvəl kişi adı ilə axtar

        for (
            const voice of voices
        ) {

            const name =
                voice.name.toLowerCase();


            for (
                const maleName of maleNames
            ) {

                if (
                    name.includes(
                        maleName.toLowerCase()
                    )
                ) {

                    maleVoice = voice;

                    break;
                }

            }

            if (maleVoice)
                break;

        }


        // Azərbaycan dili səsi varsa
        // ona üstünlük ver

        if (!maleVoice) {

            for (
                const voice of voices
            ) {

                if (
                    voice.lang
                        .toLowerCase()
                        .startsWith("az")
                ) {

                    maleVoice = voice;

                    break;
                }

            }

        }


        // İngilis kişi səsi fallback

        if (!maleVoice) {

            for (
                const voice of voices
            ) {

                const lang =
                    voice.lang
                        .toLowerCase();

                const name =
                    voice.name
                        .toLowerCase();


                if (
                    (
                        lang.includes("en")
                    )
                    &&
                    (
                        name.includes("male")
                        ||
                        name.includes("david")
                        ||
                        name.includes("daniel")
                        ||
                        name.includes("mark")
                        ||
                        name.includes("alex")
                    )
                ) {

                    maleVoice = voice;

                    break;
                }

            }

        }


        if (maleVoice) {

            speech.voice =
                maleVoice;

        }


        // ====================================================
        // KİŞİ SƏSİ ÜÇÜN PARAMETRLƏR
        // ====================================================

        speech.rate = 0.95;

        speech.pitch = 0.75;

        speech.volume = 1.0;


        speech.onend =
            function () {

                if (callback)
                    callback();

            };


        speech.onerror =
            function () {

                if (callback)
                    callback();

            };


        window.speechSynthesis
            .speak(speech);

    }


    // ========================================================
    // UI
    // ========================================================

    function wakeUI() {

        status.innerText =
            '👂 "Hey Jarvis" gözlənilir...';


        dot.style.background =
            "#ff3333";


        dot.style.boxShadow =
            "0 0 18px #ff3333";

    }


    function commandUI() {

        status.innerText =
            "🎤 Sizi dinləyirəm...";


        dot.style.background =
            "#00ffcc";


        dot.style.boxShadow =
            "0 0 30px #00ffcc";

    }


    // ========================================================
    // CREATE RECOGNITION
    // ========================================================

    function createRecognition() {

        const r =
            new SpeechRecognition();


        r.lang = "az-AZ";


        r.continuous = false;


        r.interimResults = false;


        r.maxAlternatives = 5;


        // ----------------------------------------------------
        // START
        // ----------------------------------------------------

        r.onstart =
            function () {

                listening = true;


                if (
                    mode === "wake"
                ) {

                    wakeUI();

                } else {

                    commandUI();

                }

            };


        // ----------------------------------------------------
        // RESULT
        // ----------------------------------------------------

        r.onresult =
            function (event) {

                listening = false;


                const text =
                    normalize(
                        event
                            .results[0][0]
                            .transcript
                    );


                console.log(
                    "JARVIS:",
                    text
                );


                // ============================================
                // WAKE WORD
                // ============================================

                if (
                    mode === "wake"
                ) {

                    let activated =
                        false;


                    for (
                        const word
                        of wakeWords
                    ) {

                        if (
                            text.includes(word)
                        ) {

                            activated =
                                true;

                            break;

                        }

                    }


                    if (!activated) {

                        restartWake();

                        return;

                    }


                    // Jarvis aktivləşdi

                    mode = "command";


                    status.innerText =
                        "🤖 Bəli cənab...";


                    dot.style.background =
                        "#00ffcc";


                    dot.style.boxShadow =
                        "0 0 35px #00ffcc";


                    // ====================================================
                    // JARVIS KİŞİ SƏSİ İLƏ CAVAB
                    // ====================================================

                    speakJarvis(

                        "Bəli cənab, xidmətinizdəyəm.",

                        function () {

                            setTimeout(
                                startRecognition,
                                250
                            );

                        }

                    );


                    return;

                }


                // ============================================
                // COMMAND
                // ============================================

                if (
                    mode === "command"
                ) {

                    if (!text) {

                        restartWake();

                        return;

                    }


                    status.innerText =
                        "🧠 Düşünürəm...";


                    dot.style.background =
                        "#0099ff";


                    dot.style.boxShadow =
                        "0 0 30px #0099ff";


                    // Streamlit-ə göndər

                    sendToStreamlit(
                        text
                    );


                    // Yenidən wake gözləmə

                    mode = "wake";

                }

            };


        // ----------------------------------------------------
        // ERROR
        // ----------------------------------------------------

        r.onerror =
            function (event) {

                console.log(
                    "Speech error:",
                    event.error
                );


                listening = false;


                if (
                    event.error ===
                    "not-allowed"
                ) {

                    status.innerText =
                        "❌ Mikrofon icazəsi verilməyib.";

                    dot.style.background =
                        "#ff0000";

                    return;

                }


                if (
                    mode === "wake"
                ) {

                    restartWake();

                }

            };


        // ----------------------------------------------------
        // END
        // ----------------------------------------------------

        r.onend =
            function () {

                listening = false;


                if (
                    mode === "wake"
                ) {

                    restartWake();

                }

            };


        return r;

    }


    // ========================================================
    // START
    // ========================================================

    function startRecognition() {

        if (listening)
            return;


        try {

            recognition =
                createRecognition();


            recognition.start();

        }

        catch (error) {

            console.log(
                "Recognition error:",
                error
            );

        }

    }


    // ========================================================
    // RESTART
    // ========================================================

    function restartWake() {

        if (restarting)
            return;


        restarting = true;


        mode = "wake";


        setTimeout(
            function () {

                restarting =
                    false;


                startRecognition();

            },
            700
        );

    }


    // ========================================================
    // SEND TO STREAMLIT
    // ========================================================

    function sendToStreamlit(text) {

        const input =
            window.parent.document
                .querySelector(
                    'input[aria-label="Jarvisə nəsə de..."]'
                );


        if (!input) {

            status.innerText =
                "⚠️ Mətn sahəsi tapılmadı.";

            restartWake();

            return;

        }


        const setter =
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                "value"
            ).set;


        setter.call(
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


        setTimeout(
            function () {

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


            },
            400
        );

    }


    // ========================================================
    // VOICES LOADED
    // ========================================================

    if (
        window.speechSynthesis
    ) {

        window.speechSynthesis
            .onvoiceschanged =
            function () {

                console.log(
                    "JARVIS voices loaded"
                );

            };

    }


    // ========================================================
    // START
    // ========================================================

    setTimeout(
        startRecognition,
        1000
    );


})();

</script>

</body>

</html>
        """,
        height=260
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
# TEXT INPUT
# ============================================================

with st.form(
    key="chat_form",
    clear_on_submit=True
):

    prompt = st.text_input(
        "Jarvisə nəsə de...",
        placeholder="Məsələn: Bakı haqqında məlumat ver"
    )


    submit_button = (
        st.form_submit_button(
            "➔ Göndər"
        )
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

        try:

            last_error = None


            for attempt in range(3):

                try:

                    client =
                        get_gemini_client(
                            attempt
                        )


                    response =
                        client.models.generate_content(

                            model="gemini-3.6-flash",

                            contents=prompt,

                            config=
                                types.GenerateContentConfig(

                                    system_instruction=
                                        system_instruction_text,

                                    temperature=0.1

                                )

                        )


                    if (
                        response
                        and response.text
                    ):

                        response_text =
                            response.text.strip()

                        break


                except Exception as error:

                    last_error = error


                    if attempt < 2:

                        time.sleep(2)


            if not response_text:

                response_text =
                    "⚠️ Cavab alınmadı."


        except Exception:

            response_text =
                "⚠️ Gemini API ilə əlaqə zamanı xəta baş verdi."


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

        clean_speech = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            response_text
        )


        clean_speech = (
            clean_speech
            .replace("*", "")
            .replace("#", "")
            .replace("`", "")
        )


        speech_json = json.dumps(
            clean_speech,
            ensure_ascii=False
        )


        tts_html = """

<script>

(function () {

    const text = %s;


    if (
        !window.speechSynthesis ||
        !text
    ) {

        return;

    }


    window.speechSynthesis.cancel();


    const speech =
        new SpeechSynthesisUtterance(
            text
        );


    speech.lang = "az-AZ";


    // ========================================================
    // KİŞİ SƏSİ
    // ========================================================

    const voices =
        window.speechSynthesis
            .getVoices();


    let maleVoice = null;


    const maleNames = [

        "Microsoft David",
        "Microsoft Mark",
        "Google UK English Male",
        "Google US English Male",
        "Daniel",
        "Alex",
        "Thomas",
        "Arthur",
        "Fred",
        "Male"

    ];


    for (
        const voice of voices
    ) {

        const name =
            voice.name.toLowerCase();


        for (
            const maleName of maleNames
        ) {

            if (
                name.includes(
                    maleName.toLowerCase()
                )
            ) {

                maleVoice = voice;

                break;

            }

        }


        if (maleVoice)
            break;

    }


    if (!maleVoice) {

        for (
            const voice of voices
        ) {

            if (
                voice.lang
                    .toLowerCase()
                    .startsWith("az")
            ) {

                maleVoice = voice;

                break;

            }

        }

    }


    if (maleVoice) {

        speech.voice =
            maleVoice;

    }


    speech.rate = 0.95;

    speech.pitch = 0.75;

    speech.volume = 1.0;


    window.speechSynthesis
        .speak(speech);

})();

</script>

""" % speech_json


        st.components.v1.html(
            tts_html,
            height=1
    )
