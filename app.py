import streamlit as st
from google import genai
from google.genai import types
import time
import json
import re

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

    key = None

    if (
        attempt_index % 2 == 1
        and "GEMINI_API_KEY_2" in st.secrets
    ):
        key = st.secrets["GEMINI_API_KEY_2"]

    else:
        key = st.secrets.get(
            "GEMINI_API_KEY_1",
            st.secrets.get("GEMINI_API_KEY")
        )

    if not key:
        raise ValueError(
            "GEMINI API key tapılmadı."
        )

    return genai.Client(
        api_key=key
    )


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_started" not in st.session_state:
    st.session_state.voice_started = False


# ============================================================
# JARVIS SYSTEM INSTRUCTION
# ============================================================

system_instruction_text = """
Sən Jarvis adlı şəxsi süni intellekt köməkçisisən.

İstifadəçi ilə əsasən Azərbaycan dilində danış.

Sənin üslubun:
- ağıllı
- nəzakətli
- sürətli
- qısa
- konkret
- təbii

İstifadəçiyə lazım olmayan uzun izahlar vermə.

İstifadəçi sənə adi sual verirsə, birbaşa cavab ver.

İstifadəçi sənə "cənab" deyə müraciət edə bilər.
Sən də lazım olduqda nəzakətli şəkildə "cənab" ifadəsindən istifadə edə bilərsən.

Özünü Jarvis kimi apar.
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

                if len(preview) > 35:
                    preview = preview[:35] + "..."

                st.write(
                    "▫️ " + preview
                )

    else:

        st.caption(
            "Hələ ki söhbət yoxdur."
        )


# ============================================================
# TITLE
# ============================================================

st.title("🤖 Jarvis AI")

st.caption(
    'Səsli rejim: "Hey Jarvis"'
)


# ============================================================
# ACTIVATE VOICE
# ============================================================

if not st.session_state.voice_started:

    st.info(
        'Jarvis-i səsli istifadə etmək üçün '
        '"JARVIS-i AKTİVLƏŞDİR" düyməsinə basın.'
    )

    if st.button(
        "🤖 JARVIS-i AKTİVLƏŞDİR",
        use_container_width=True,
        type="primary"
    ):

        st.session_state.voice_started = True

        st.rerun()


# ============================================================
# VOICE ENGINE
# ============================================================

if st.session_state.voice_started:

    st.components.v1.html(
        """
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<style>

.jarvis-box {

    background:
        linear-gradient(
            145deg,
            #0b0b0b,
            #191919
        );

    color: white;

    padding: 22px;

    border-radius: 20px;

    text-align: center;

    font-family: Arial, sans-serif;

    border: 2px solid #00ffcc;

    box-shadow:
        0 0 25px rgba(0,255,204,0.15);

}

.jarvis-logo {

    font-size: 48px;

}

.jarvis-title {

    color: #00ffcc;

    font-size: 27px;

    font-weight: bold;

    margin-top: 5px;

}

.jarvis-status {

    color: #aaa;

    font-size: 15px;

}

#jarvisDot {

    width: 18px;

    height: 18px;

    border-radius: 50%;

    background: #ff3333;

    margin: 18px auto;

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

    <p
        id="jarvisStatus"
        class="jarvis-status"
    >
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
            "❌ Bu brauzer səs tanımanı dəstəkləmir.";

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
    // UI - WAKE
    // ========================================================

    function wakeUI() {

        status.innerText =
            '👂 "Hey Jarvis" gözlənilir...';

        dot.style.background =
            "#ff3333";

        dot.style.boxShadow =
            "0 0 18px #ff3333";

    }


    // ========================================================
    // UI - COMMAND
    // ========================================================

    function commandUI() {

        status.innerText =
            "🎤 Sizi dinləyirəm...";

        dot.style.background =
            "#00ffcc";

        dot.style.boxShadow =
            "0 0 30px #00ffcc";

    }


    // ========================================================
    // FIND MALE VOICE
    // ========================================================

    function findMaleVoice() {

        const voices =
            window.speechSynthesis.getVoices();


        if (!voices.length) {
            return null;
        }


        const maleNames = [

            "Microsoft David",
            "Microsoft Mark",
            "Microsoft George",
            "David",
            "Mark",
            "George",
            "Daniel",
            "Alex",
            "Thomas",
            "Arthur",
            "Fred",
            "Male"

        ];


        // ----------------------------------------------------
        // 1. KİŞİ ADI İLƏ AXTAR
        // ----------------------------------------------------

        for (
            const voice of voices
        ) {

            const name =
                voice.name.toLowerCase();


            for (
                const maleName
                of maleNames
            ) {

                if (
                    name.includes(
                        maleName.toLowerCase()
                    )
                ) {

                    return voice;

                }

            }

        }


        // ----------------------------------------------------
        // 2. ENGLISH MALE FALLBACK
        // ----------------------------------------------------

        for (
            const voice of voices
        ) {

            const name =
                voice.name.toLowerCase();

            const lang =
                voice.lang.toLowerCase();


            if (
                lang.startsWith("en")
                &&
                (
                    name.includes("male")
                    ||
                    name.includes("david")
                    ||
                    name.includes("mark")
                    ||
                    name.includes("daniel")
                    ||
                    name.includes("george")
                    ||
                    name.includes("alex")
                )
            ) {

                return voice;

            }

        }


        // ----------------------------------------------------
        // 3. AZƏRBAYCAN DİLİ
        // ----------------------------------------------------

        for (
            const voice of voices
        ) {

            if (
                voice.lang
                    .toLowerCase()
                    .startsWith("az")
            ) {

                return voice;

            }

        }


        return null;

    }


    // ========================================================
    // JARVIS SPEAK
    // ========================================================

    function speakJarvis(
        text,
        callback
    ) {

        if (
            !window.speechSynthesis
        ) {

            if (callback) {
                callback();
            }

            return;
        }


        window.speechSynthesis.cancel();


        const speech =
            new SpeechSynthesisUtterance(
                text
            );


        speech.lang = "az-AZ";


        // ----------------------------------------------------
        // KİŞİ SƏSİ
        // ----------------------------------------------------

        const voice =
            findMaleVoice();


        if (voice) {

            speech.voice = voice;

        }


        // ----------------------------------------------------
        // JARVIS SƏS PARAMETRLƏRİ
        // ----------------------------------------------------

        speech.rate = 0.92;

        speech.pitch = 0.72;

        speech.volume = 1.0;


        speech.onend =
            function () {

                if (callback) {
                    callback();
                }

            };


        speech.onerror =
            function () {

                if (callback) {
                    callback();
                }

            };


        window.speechSynthesis.speak(
            speech
        );

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
                    "Jarvis eşitdi:",
                    text
                );


                // =================================================
                // WAKE MODE
                // =================================================

                if (
                    mode === "wake"
                ) {

                    let activated = false;


                    for (
                        const word
                        of wakeWords
                    ) {

                        if (
                            text.includes(word)
                        ) {

                            activated = true;

                            break;

                        }

                    }


                    if (!activated) {

                        restartWake();

                        return;

                    }


                    // ------------------------------------------------
                    // JARVIS AKTİVLƏŞDİ
                    // ------------------------------------------------

                    mode = "command";


                    status.innerText =
                        "🤖 Bəli cənab...";


                    dot.style.background =
                        "#00ffcc";


                    dot.style.boxShadow =
                        "0 0 35px #00ffcc";


                    // ------------------------------------------------
                    // JARVIS CAVABI
                    // ------------------------------------------------

                    speakJarvis(

                        "Bəli cənab, xidmətinizdəyəm.",

                        function () {

                            setTimeout(
                                function () {

                                    startRecognition();

                                },
                                300
                            );

                        }

                    );


                    return;

                }


                // =================================================
                // COMMAND MODE
                // =================================================

                if (
                    mode === "command"
                ) {

                    if (!text) {

                        mode = "wake";

                        restartWake();

                        return;

                    }


                    status.innerText =
                        "🧠 Sorğunuz göndərilir...";


                    dot.style.background =
                        "#0088ff";


                    dot.style.boxShadow =
                        "0 0 30px #0088ff";


                    // ------------------------------------------------
                    // STREAMLIT
                    // ------------------------------------------------

                    sendToStreamlit(
                        text
                    );


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
    // START RECOGNITION
    // ========================================================

    function startRecognition() {

        if (listening) {
            return;
        }


        try {

            recognition =
                createRecognition();


            recognition.start();

        }

        catch (error) {

            console.log(
                "Recognition start error:",
                error
            );

        }

    }


    // ========================================================
    // RESTART WAKE
    // ========================================================

    function restartWake() {

        if (restarting) {
            return;
        }


        restarting = true;

        mode = "wake";


        setTimeout(
            function () {

                restarting = false;

                startRecognition();

            },
            800
        );

    }


    // ========================================================
    // SEND TO STREAMLIT
    // ========================================================

    function sendToStreamlit(text) {

        const parent =
            window.parent.document;


        const input =
            parent.querySelector(
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
            500
        );

    }


    // ========================================================
    // LOAD VOICES
    // ========================================================

    if (
        window.speechSynthesis
    ) {

        window.speechSynthesis
            .getVoices();


        window.speechSynthesis
            .onvoiceschanged =
            function () {

                window.speechSynthesis
                    .getVoices();

            };

    }


    // ========================================================
    // START JARVIS
    // ========================================================

    setTimeout(
        function () {

            startRecognition();

        },
        1200
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
            key=f"action_{idx}",
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
        placeholder=(
            "Məsələn: Bakı haqqında məlumat ver"
        )
    )


    submit_button = st.form_submit_button(
        "➔ Göndər"
    )


# ============================================================
# GEMINI REQUEST
# ============================================================

if submit_button and prompt:

    # --------------------------------------------------------
    # USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    with st.chat_message("user"):

        st.markdown(prompt)


    # --------------------------------------------------------
    # ASSISTANT
    # --------------------------------------------------------

    with st.chat_message("assistant"):

        response_text = None


        # ====================================================
        # GEMINI RETRIES
        # ====================================================

        for attempt in range(3):

            try:

                client = get_gemini_client(
                    attempt
                )


                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            system_instruction_text
                        ),
                        temperature=0.2
                    )
                )


                if (
                    response
                    and response.text
                ):

                    response_text = (
                        response.text.strip()
                    )

                    break


            except Exception as error:

                print(
                    "Gemini error:",
                    error
                )


                if attempt < 2:

                    time.sleep(2)


        # ====================================================
        # ERROR
        # ====================================================

        if not response_text:

            response_text = (
                "Bağışlayın cənab, "
                "hazırda cavab ala bilmədim."
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        st.markdown(
            response_text,
            unsafe_allow_html=True
        )


        # ====================================================
        # SAVE
        # ====================================================

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
        !text ||
        !window.speechSynthesis
    ) {

        return;

    }


    function speak() {

        window.speechSynthesis.cancel();


        const speech =
            new SpeechSynthesisUtterance(
                text
            );


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
            "Microsoft George",
            "David",
            "Mark",
            "George",
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
                const maleName
                of maleNames
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


            if (maleVoice) {
                break;
            }

        }


        // ====================================================
        // AZƏRBAYCAN DİLİ FALLBACK
        // ====================================================

        if (!maleVoice) {

            for (
                const voice of voices
            ) {

                if (
                    voice.lang &&
                    voice.lang
                        .toLowerCase()
                        .startsWith("az")
                ) {

                    maleVoice = voice;

                    break;

                }

            }

        }


        // ====================================================
        // ENGLISH MALE FALLBACK
        // ====================================================

        if (!maleVoice) {

            for (
                const voice of voices
            ) {

                const name =
                    voice.name.toLowerCase();

                const lang =
                    voice.lang.toLowerCase();


                if (
                    lang.startsWith("en")
                    &&
                    (
                        name.includes("male")
                        ||
                        name.includes("david")
                        ||
                        name.includes("mark")
                        ||
                        name.includes("daniel")
                        ||
                        name.includes("george")
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
        // JARVIS VOICE
        // ====================================================

        speech.rate = 0.92;

        speech.pitch = 0.72;

        speech.volume = 1.0;


        window.speechSynthesis
            .speak(speech);

    }


    // Android Chrome-də səslərin
    // yüklənməsini gözlə

    const voices =
        window.speechSynthesis
            .getVoices();


    if (voices.length > 0) {

        speak();

    } else {

        window.speechSynthesis
            .onvoiceschanged =
            function () {

                window.speechSynthesis
                    .onvoiceschanged = null;

                speak();

            };

    }

})();

</script>
""" % speech_json


        st.components.v1.html(
            tts_html,
            height=1
    )
