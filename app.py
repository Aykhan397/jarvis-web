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
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONFIG
# ============================================================

MODEL_NAME = "gemini-3.7-flash"

SYSTEM_INSTRUCTION = """
Sən JARVIS adlı şəxsi süni intellekt köməkçisisən.

İstifadəçi ilə əsasən Azərbaycan dilində danış.

Davranışın:
- ağıllı
- nəzakətli
- sürətli
- konkret
- təbii
- köməkçi

Cavabları lazımsız yerə uzatma.
Sadə suallara qısa və aydın cavab ver.

İstifadəçi sənə "cənab" deyə müraciət edə bilər.
Uyğun olduqda sən də "cənab" deyə müraciət edə bilərsən.

Özünü JARVIS kimi apar.
Amma özünü real insan kimi təqdim etmə.

Əgər istifadəçi Azərbaycan dilində danışırsa,
Azərbaycan dilində cavab ver.

Əgər istifadəçi başqa dildə danışırsa,
mümkün olduqda həmin dildə cavab ver.
"""


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_api_keys():

    keys = []

    key1 = st.secrets.get("GEMINI_API_KEY_1")
    key2 = st.secrets.get("GEMINI_API_KEY_2")
    key_default = st.secrets.get("GEMINI_API_KEY")

    if key1:
        keys.append(key1)

    if key2:
        keys.append(key2)

    if key_default and key_default not in keys:
        keys.append(key_default)

    return keys


def get_gemini_client(attempt_index=0):

    keys = get_api_keys()

    if not keys:
        raise ValueError(
            "Gemini API key tapılmadı.\n\n"
            "Streamlit Secrets bölməsinə "
            "GEMINI_API_KEY əlavə edin."
        )

    key = keys[attempt_index % len(keys)]

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

if "last_response" not in st.session_state:
    st.session_state.last_response = ""


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.jarvis-header {
    text-align: center;
    padding: 12px 10px 5px 10px;
}

.jarvis-header h1 {
    font-size: 44px;
    margin: 0;
    font-weight: 800;
    letter-spacing: 4px;
}

.jarvis-header p {
    color: #888;
    margin-top: 5px;
}

div.stButton > button {
    border-radius: 12px;
    min-height: 45px;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💬 Söhbətlər")

    if st.button(
        "➕ Yeni söhbət",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.last_response = ""

        st.rerun()

    st.markdown("---")

    st.subheader("Keçmiş suallar")

    user_messages = [
        m
        for m in st.session_state.messages
        if m["role"] == "user"
    ]

    if user_messages:

        for message in user_messages:

            text = message["content"]

            if len(text) > 45:
                text = text[:45] + "..."

            st.write("▫️ " + text)

    else:

        st.caption(
            "Hələ heç bir sual yoxdur."
        )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="jarvis-header">
    <h1>🤖 JARVIS AI</h1>
    <p>Səsli şəxsi süni intellekt köməkçiniz</p>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# VOICE ACTIVATION
# ============================================================

if not st.session_state.voice_started:

    st.info(
        '🎤 Başlamaq üçün düyməyə basın. '
        'Sonra "Hey Jarvis" deyin.'
    )

    if st.button(
        "🤖 JARVIS-İ AKTİVLƏŞDİR",
        type="primary",
        use_container_width=True
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

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
/>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: Arial, sans-serif;
}

.jarvis-box {

    width: 100%;

    padding: 28px 20px;

    border-radius: 24px;

    background:
        radial-gradient(
            circle at center,
            #102b2b 0%,
            #0a1111 45%,
            #050505 100%
        );

    border: 1px solid
        rgba(0,255,213,0.7);

    color: white;

    text-align: center;

    box-shadow:
        0 0 35px
        rgba(0,255,213,0.14);

}

.robot {
    font-size: 55px;
    line-height: 1;
}

.title {

    margin-top: 10px;

    font-size: 30px;

    font-weight: 800;

    letter-spacing: 5px;

    color: #00ffd5;

    text-shadow:
        0 0 15px
        rgba(0,255,213,0.4);

}

.status {

    margin-top: 10px;

    color: #aaa;

    font-size: 15px;

    min-height: 22px;

}

.dot {

    width: 22px;

    height: 22px;

    border-radius: 50%;

    margin: 20px auto 5px;

    background: #ff3333;

    box-shadow:
        0 0 22px
        rgba(255,51,51,0.8);

    transition:
        background 0.2s,
        box-shadow 0.2s;

}

.hint {

    margin-top: 14px;

    color: #666;

    font-size: 12px;

}

</style>

</head>

<body>

<div class="jarvis-box">

    <div class="robot">
        🤖
    </div>

    <div class="title">
        JARVIS
    </div>

    <div
        id="status"
        class="status"
    >
        Başlayır...
    </div>

    <div
        id="dot"
        class="dot"
    ></div>

    <div class="hint">
        "Hey Jarvis" deyin
    </div>

</div>


<script>

(function () {

"use strict";


/* =========================================================
   ELEMENTS
========================================================= */

const status =
    document.getElementById("status");

const dot =
    document.getElementById("dot");


/* =========================================================
   SPEECH API
========================================================= */

const Recognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


/* =========================================================
   CHECK SUPPORT
========================================================= */

if (!Recognition) {

    status.innerText =
        "❌ Bu brauzerdə səs tanıma dəstəklənmir.";

    dot.style.background = "#ff0000";

    return;
}


/* =========================================================
   VARIABLES
========================================================= */

let recognition = null;

let running = false;

let starting = false;

let mode = "wake";

let destroyed = false;

let restartTimer = null;

let commandTimeout = null;


/* =========================================================
   WAKE WORDS
========================================================= */

const wakeWords = [

    "hey jarvis",
    "hey, jarvis",
    "hey jervis",
    "hey cervis",
    "hey carvis",
    "hey jarvis",
    "ey jarvis",
    "jarvis"

];


/* =========================================================
   NORMALIZE
========================================================= */

function normalize(text) {

    return String(text || "")
        .toLowerCase()
        .replace(/[.,!?;:()[\\]{}]/g, " ")
        .replace(/\\s+/g, " ")
        .trim();

}


/* =========================================================
   UI
========================================================= */

function setStatus(text) {

    status.innerText = text;

}


function wakeUI() {

    setStatus(
        '👂 "Hey Jarvis" gözlənilir...'
    );

    dot.style.background = "#ff3333";

    dot.style.boxShadow =
        "0 0 25px rgba(255,51,51,0.9)";

}


function listeningUI() {

    setStatus(
        "🎤 Sizi dinləyirəm..."
    );

    dot.style.background = "#00ffd5";

    dot.style.boxShadow =
        "0 0 40px rgba(0,255,213,0.9)";

}


function thinkingUI() {

    setStatus(
        "🧠 Düşünürəm..."
    );

    dot.style.background = "#4285ff";

    dot.style.boxShadow =
        "0 0 40px rgba(66,133,255,0.9)";

}


/* =========================================================
   WAKE WORD
========================================================= */

function hasWakeWord(text) {

    const clean =
        normalize(text);

    return wakeWords.some(
        word =>
            clean.includes(
                normalize(word)
            )
    );

}


/* =========================================================
   REMOVE WAKE WORD
========================================================= */

function removeWakeWord(text) {

    let result =
        normalize(text);

    for (
        const word of wakeWords
    ) {

        result =
            result.replace(
                normalize(word),
                " "
            );

    }

    return result
        .replace(/\\s+/g, " ")
        .trim();

}


/* =========================================================
   MALE VOICE
========================================================= */

function getMaleVoice() {

    if (
        !window.speechSynthesis
    ) {
        return null;
    }

    const voices =
        window.speechSynthesis
            .getVoices();

    if (!voices.length) {
        return null;
    }


    const maleNames = [

        "Microsoft David",
        "Microsoft Mark",
        "Microsoft George",
        "Microsoft Ryan",
        "Google US English",
        "David",
        "Mark",
        "George",
        "Ryan",
        "Daniel",
        "Thomas",
        "Arthur",
        "Alex",
        "Fred"

    ];


    /* =====================================================
       PREFERRED MALE VOICES
    ===================================================== */

    for (
        const name of maleNames
    ) {

        const voice =
            voices.find(
                v =>
                    v.name
                    .toLowerCase()
                    .includes(
                        name.toLowerCase()
                    )
            );

        if (voice) {
            return voice;
        }

    }


    /* =====================================================
       AZERBAIJANI
    ===================================================== */

    const azVoice =
        voices.find(
            v =>
                v.lang &&
                v.lang
                    .toLowerCase()
                    .startsWith("az")
        );

    if (azVoice) {
        return azVoice;
    }


    /* =====================================================
       ENGLISH
    ===================================================== */

    const englishVoice =
        voices.find(
            v =>
                v.lang &&
                v.lang
                    .toLowerCase()
                    .startsWith("en")
        );

    if (englishVoice) {
        return englishVoice;
    }


    return voices[0];

}


/* =========================================================
   SPEAK
========================================================= */

function speak(text, callback) {

    if (
        !window.speechSynthesis
    ) {

        if (callback) {
            callback();
        }

        return;
    }


    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(
            text
        );


    const voice =
        getMaleVoice();


    if (voice) {

        utterance.voice =
            voice;

    }


    utterance.lang = "az-AZ";

    utterance.rate = 0.88;

    utterance.pitch = 0.72;

    utterance.volume = 1.0;


    utterance.onend =
        function () {

            if (callback) {
                callback();
            }

        };


    utterance.onerror =
        function () {

            if (callback) {
                callback();
            }

        };


    window.speechSynthesis
        .speak(utterance);

}


/* =========================================================
   FIND STREAMLIT INPUT
========================================================= */

function findInput() {

    const parent =
        window.parent.document;


    const inputs =
        Array.from(
            parent.querySelectorAll(
                "input"
            )
        );


    for (
        const input of inputs
    ) {

        const placeholder =
            (
                input.getAttribute(
                    "placeholder"
                ) || ""
            ).toLowerCase();


        const aria =
            (
                input.getAttribute(
                    "aria-label"
                ) || ""
            ).toLowerCase();


        if (
            placeholder.includes(
                "jarvis"
            )
            ||
            aria.includes(
                "jarvis"
            )
        ) {

            return input;

        }

    }


    return inputs.find(
        input =>
            input.type === "text"
    ) || null;

}


/* =========================================================
   SEND COMMAND TO STREAMLIT
========================================================= */

function sendToStreamlit(text) {

    const clean =
        normalize(text);


    if (!clean) {

        mode = "wake";

        restartRecognition();

        return;

    }


    thinkingUI();


    const input =
        findInput();


    if (!input) {

        setStatus(
            "⚠️ Mətn sahəsi tapılmadı."
        );

        mode = "wake";

        restartRecognition();

        return;

    }


    try {

        const setter =
            Object.getOwnPropertyDescriptor(
                HTMLInputElement.prototype,
                "value"
            ).set;


        setter.call(
            input,
            clean
        );


        input.dispatchEvent(
            new Event(
                "input",
                {
                    bubbles: true
                }
            )
        );


        input.dispatchEvent(
            new Event(
                "change",
                {
                    bubbles: true
                }
            )
        );


        setTimeout(
            function () {

                const form =
                    input.closest("form");


                if (form) {

                    const submitButton =
                        form.querySelector(
                            'button[type="submit"]'
                        );


                    if (submitButton) {

                        submitButton.click();

                        return;

                    }

                }


                input.focus();


                input.dispatchEvent(
                    new KeyboardEvent(
                        "keydown",
                        {
                            key: "Enter",
                            code: "Enter",
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        }
                    )
                );


                input.dispatchEvent(
                    new KeyboardEvent(
                        "keyup",
                        {
                            key: "Enter",
                            code: "Enter",
                            keyCode: 13,
                            which: 13,
                            bubbles: true
                        }
                    )
                );

            },
            300
        );


    } catch (error) {

        console.error(
            "Streamlit input error:",
            error
        );

        setStatus(
            "⚠️ Komanda göndərilə bilmədi."
        );

    }


    mode = "wake";


    clearTimeout(
        commandTimeout
    );


    commandTimeout =
        setTimeout(
            function () {

                restartRecognition();

            },
            2200
        );

}


/* =========================================================
   CREATE RECOGNITION
========================================================= */

function createRecognition() {

    const r =
        new Recognition();


    /*
       Azərbaycan dili.
       Əgər cihazda problem yaranarsa,
       brauzer öz dəstəklədiyi sistemi istifadə edir.
    */

    r.lang = "az-AZ";

    r.continuous = false;

    r.interimResults = false;

    r.maxAlternatives = 5;


    /* =====================================================
       START
    ===================================================== */

    r.onstart =
        function () {

            running = true;

            starting = false;


            if (
                mode === "wake"
            ) {

                wakeUI();

            } else {

                listeningUI();

            }

        };


    /* =====================================================
       RESULT
    ===================================================== */

    r.onresult =
        function (event) {

            running = false;


            let bestText = "";


            if (
                !event.results ||
                !event.results.length
            ) {

                restartRecognition();

                return;

            }


            const result =
                event.results[
                    event.results.length - 1
                ];


            /*
               Ən uyğun nəticəni seç.
            */

            for (
                let i = 0;
                i < result.length;
                i++
            ) {

                const transcript =
                    normalize(
                        result[i].transcript
                    );


                if (!transcript) {
                    continue;
                }


                if (
                    !bestText
                ) {

                    bestText =
                        transcript;

                }


                if (
                    mode === "wake" &&
                    hasWakeWord(
                        transcript
                    )
                ) {

                    bestText =
                        transcript;

                    break;

                }

            }


            console.log(
                "JARVIS eşitdi:",
                bestText
            );


            /* =================================================
               WAKE MODE
            ================================================= */

            if (
                mode === "wake"
            ) {

                if (
                    !hasWakeWord(
                        bestText
                    )
                ) {

                    restartRecognition();

                    return;

                }


                mode = "command";


                const command =
                    removeWakeWord(
                        bestText
                    );


                /*
                   "Hey Jarvis, hava necədir?"
                */

                if (command) {

                    sendToStreamlit(
                        command
                    );

                    return;

                }


                /*
                   Sadəcə "Hey Jarvis"
                */

                setStatus(
                    "🤖 Bəli cənab..."
                );


                dot.style.background =
                    "#00ffd5";


                dot.style.boxShadow =
                    "0 0 45px rgba(0,255,213,1)";


                speak(
                    "Bəli cənab, xidmətinizdəyəm.",
                    function () {

                        mode =
                            "command";


                        setTimeout(
                            function () {

                                startRecognition();

                            },
                            250
                        );

                    }
                );


                return;

            }


            /* =================================================
               COMMAND MODE
            ================================================= */

            if (
                mode === "command"
            ) {

                if (!bestText) {

                    mode = "wake";

                    restartRecognition();

                    return;

                }


                sendToStreamlit(
                    bestText
                );

            }

        };


    /* =====================================================
       ERROR
    ===================================================== */

    r.onerror =
        function (event) {

            console.log(
                "Speech error:",
                event.error
            );


            running = false;

            starting = false;


            if (
                event.error ===
                "not-allowed"
            ) {

                setStatus(
                    "❌ Mikrofon icazəsi verilməyib."
                );

                dot.style.background =
                    "#ff0000";

                dot.style.boxShadow =
                    "0 0 30px #ff0000";

                return;

            }


            if (
                event.error ===
                "service-not-allowed"
            ) {

                setStatus(
                    "❌ Brauzerin səs xidməti əlçatan deyil."
                );

                return;

            }


            if (
                event.error ===
                "audio-capture"
            ) {

                setStatus(
                    "❌ Mikrofon tapılmadı."
                );

                return;

            }


            /*
               no-speech normal haldır.
            */

            if (
                event.error ===
                "no-speech"
            ) {

                restartRecognition();

                return;

            }


            if (
                event.error ===
                "aborted"
            ) {

                return;

            }


            restartRecognition();

        };


    /* =====================================================
       END
    ===================================================== */

    r.onend =
        function () {

            running = false;

            starting = false;


            if (destroyed) {
                return;
            }


            if (
                mode === "wake"
            ) {

                restartRecognition();

            }

        };


    return r;

}


/* =========================================================
   START RECOGNITION
========================================================= */

function startRecognition() {

    if (
        destroyed ||
        running ||
        starting
    ) {

        return;

    }


    starting = true;


    try {

        recognition =
            createRecognition();


        recognition.start();


    } catch (error) {

        console.log(
            "Recognition start error:",
            error
        );


        running = false;

        starting = false;


        clearTimeout(
            restartTimer
        );


        restartTimer =
            setTimeout(
                function () {

                    startRecognition();

                },
                1000
            );

    }

}


/* =========================================================
   RESTART RECOGNITION
========================================================= */

function restartRecognition() {

    if (destroyed) {
        return;
    }


    clearTimeout(
        restartTimer
    );


    if (recognition) {

        try {

            recognition.stop();

        } catch (e) {}

    }


    running = false;

    starting = false;


    restartTimer =
        setTimeout(
            function () {

                if (
                    mode !== "wake"
                ) {

                    mode = "wake";

                }


                startRecognition();

            },
            650
        );

}


/* =========================================================
   VOICE LOAD
========================================================= */

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


/* =========================================================
   START
========================================================= */

setTimeout(
    function () {

        wakeUI();

        startRecognition();

    },
    900
);


})();

</script>

</body>

</html>
        """,
        height=300,
        scrolling=False
    )


# ============================================================
# CHAT HISTORY
# ============================================================

st.markdown("---")


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"],
            unsafe_allow_html=True
        )


# ============================================================
# TEXT INPUT
# ============================================================

with st.form(
    "chat_form",
    clear_on_submit=True
):

    prompt = st.text_input(
        "Jarvisə nəsə de...",
        placeholder=(
            "Məsələn: Bakı haqqında məlumat ver"
        ),
        label_visibility="visible"
    )


    submit = st.form_submit_button(
        "➜ Göndər",
        use_container_width=True
    )


# ============================================================
# GEMINI
# ============================================================

if submit and prompt.strip():

    prompt =
        prompt.strip()


    # ========================================================
    # USER MESSAGE
    # ========================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )


    with st.chat_message("user"):

        st.markdown(
            prompt
        )


    # ========================================================
    # ASSISTANT
    # ========================================================

    with st.chat_message("assistant"):

        response_text = None

        last_error = None


        # ====================================================
        # BUILD CONVERSATION HISTORY
        # ====================================================

        contents = []


        for message in st.session_state.messages:

            role =
                message["role"]


            text =
                message["content"]


            contents.append(
                types.Content(
                    role=(
                        "user"
                        if role == "user"
                        else "model"
                    ),
                    parts=[
                        types.Part.from_text(
                            text=text
                        )
                    ]
                )
            )


        # ====================================================
        # API RETRIES
        # ====================================================

        for attempt in range(4):

            try:

                client =
                    get_gemini_client(
                        attempt
                    )


                response =
                    client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=
                            types.GenerateContentConfig(
                                system_instruction=
                                    SYSTEM_INSTRUCTION,

                                temperature=0.25,

                                max_output_tokens=1200
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

                last_error =
                    str(error)

                print(
                    "Gemini error:",
                    error
                )


                if attempt < 3:

                    time.sleep(
                        1.5
                    )


        # ====================================================
        # FALLBACK
        # ====================================================

        if not response_text:

            response_text = (
                "Bağışlayın cənab, "
                "hazırda Gemini xidmətindən "
                "cavab ala bilmədim."
            )


        # ====================================================
        # SHOW RESPONSE
        # ====================================================

        st.markdown(
            response_text,
            unsafe_allow_html=True
        )


        # ====================================================
        # SAVE RESPONSE
        # ====================================================

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response_text
            }
        )


        st.session_state.last_response =
            response_text


        # ====================================================
        # CLEAN TEXT FOR SPEECH
        # ====================================================

        clean_speech =
            response_text


        # Markdown links
        clean_speech =
            re.sub(
                r"\[([^\]]+)\]\([^)]+\)",
                r"\1",
                clean_speech
            )


        # Code blocks
        clean_speech =
            re.sub(
                r"```[\s\S]*?```",
                "",
                clean_speech
            )


        # Markdown symbols
        clean_speech =
            re.sub(
                r"[*_#>`~]",
                "",
                clean_speech
            )


        # Multiple spaces
        clean_speech =
            re.sub(
                r"\s+",
                " ",
                clean_speech
            ).strip()


        speech_json =
            json.dumps(
                clean_speech,
                ensure_ascii=False
            )


        # ====================================================
        # TEXT TO SPEECH
        # ====================================================

        st.components.v1.html(
            f"""
<script>

(function() {{

"use strict";


const text =
    {speech_json};


if (
    !text ||
    !window.speechSynthesis
) {{
    return;
}}


/* =========================================================
   VOICE SELECTION
========================================================= */

function findMaleVoice() {{

    const voices =
        window.speechSynthesis
            .getVoices();


    if (!voices.length) {{
        return null;
    }}


    const preferred = [

        "Microsoft David",
        "Microsoft Mark",
        "Microsoft George",
        "Microsoft Ryan",
        "David",
        "Mark",
        "George",
        "Ryan",
        "Daniel",
        "Thomas",
        "Arthur",
        "Alex"

    ];


    for (
        const wanted
        of preferred
    ) {{

        const found =
            voices.find(
                v =>
                    v.name
                    .toLowerCase()
                    .includes(
                        wanted.toLowerCase()
                    )
            );


        if (found) {{
            return found;
        }}

    }}


    const az =
        voices.find(
            v =>
                v.lang &&
                v.lang
                    .toLowerCase()
                    .startsWith("az")
        );


    if (az) {{
        return az;
    }}


    const english =
        voices.find(
            v =>
                v.lang &&
                v.lang
                    .toLowerCase()
                    .startsWith("en")
        );


    if (english) {{
        return english;
    }}


    return voices[0];

}}


/* =========================================================
   SPEAK
========================================================= */

function speak() {{

    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(
            text
        );


    const voice =
        findMaleVoice();


    if (voice) {{
        utterance.voice =
            voice;
    }}


    utterance.lang =
        "az-AZ";


    utterance.rate =
        0.88;


    utterance.pitch =
        0.72;


    utterance.volume =
        1.0;


    window.speechSynthesis
        .speak(
            utterance
        );

}}


/* =========================================================
   VOICES MAY LOAD LATE
========================================================= */

const voices =
    window.speechSynthesis
        .getVoices();


if (voices.length) {{

    setTimeout(
        speak,
        150
    );

}} else {{

    window.speechSynthesis
        .onvoiceschanged =
        function() {{

            window.speechSynthesis
                .onvoiceschanged =
                null;


            setTimeout(
                speak,
                100
            );

        }};

}}

}})();

</script>
""",
            height=1,
            scrolling=False
    )
