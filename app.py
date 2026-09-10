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
# GEMINI
# ============================================================

def get_gemini_client(attempt_index=0):

    key = None

    if attempt_index % 2 == 1:
        key = st.secrets.get("GEMINI_API_KEY_2")

    if not key:
        key = st.secrets.get(
            "GEMINI_API_KEY_1",
            st.secrets.get("GEMINI_API_KEY")
        )

    if not key:
        raise ValueError(
            "GEMINI API key tapılmadı. "
            "Secrets bölməsinə GEMINI_API_KEY əlavə edin."
        )

    return genai.Client(api_key=key)


# ============================================================
# SESSION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_started" not in st.session_state:
    st.session_state.voice_started = False


# ============================================================
# JARVIS SYSTEM
# ============================================================

SYSTEM_INSTRUCTION = """
Sən Jarvis adlı şəxsi süni intellekt köməkçisisən.

İstifadəçi ilə əsasən Azərbaycan dilində danış.

Üslubun:
- ağıllı
- nəzakətli
- sürətli
- konkret
- təbii

Cavabları lazımsız yerə uzatma.

İstifadəçi sənə "cənab" deyə müraciət edə bilər.
Uyğun olduqda sən də "cənab" deyə müraciət edə bilərsən.

Özünü Jarvis kimi apar.
"""


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.jarvis-header {
    text-align: center;
    padding: 10px;
}

.jarvis-header h1 {
    font-size: 42px;
    margin-bottom: 0;
}

.jarvis-header p {
    color: #888;
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
        st.rerun()

    st.markdown("---")

    st.subheader("Keçmiş suallar")

    user_messages = [
        m for m in st.session_state.messages
        if m["role"] == "user"
    ]

    if user_messages:

        for message in user_messages:

            text = message["content"]

            if len(text) > 40:
                text = text[:40] + "..."

            st.write("▫️ " + text)

    else:

        st.caption("Hələ söhbət yoxdur.")


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
# VOICE ENGINE
# ============================================================

if not st.session_state.voice_started:

    st.info(
        'Başlamaq üçün aşağıdakı düyməyə basın. '
        'Sonra "Hey Jarvis" deyin.'
    )

    if st.button(
        "🤖 JARVIS-İ AKTİVLƏŞDİR",
        type="primary",
        use_container_width=True
    ):

        st.session_state.voice_started = True
        st.rerun()


if st.session_state.voice_started:

    st.components.v1.html(
        """
<!DOCTYPE html>

<html>

<head>

<meta name="viewport"
content="width=device-width, initial-scale=1">

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: transparent;
    font-family: Arial, sans-serif;
}

.jarvis {

    width: 100%;

    padding: 25px;

    border-radius: 22px;

    background:
        radial-gradient(
            circle at center,
            #132a2a,
            #090909 70%
        );

    border: 1px solid #00ffd5;

    text-align: center;

    color: white;

    box-shadow:
        0 0 30px
        rgba(0,255,213,0.15);

}

.logo {

    font-size: 55px;

    margin-bottom: 5px;

}

.title {

    font-size: 30px;

    font-weight: bold;

    color: #00ffd5;

    letter-spacing: 3px;

}

.status {

    margin-top: 10px;

    color: #aaa;

    font-size: 15px;

}

.dot {

    width: 20px;

    height: 20px;

    border-radius: 50%;

    background: #ff3333;

    margin: 20px auto 5px;

    box-shadow:
        0 0 20px #ff3333;

}

.hint {

    margin-top: 12px;

    color: #666;

    font-size: 12px;

}

</style>

</head>


<body>


<div class="jarvis">

    <div class="logo">🤖</div>

    <div class="title">JARVIS</div>

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
   SPEECH RECOGNITION
========================================================= */

const Recognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


if (!Recognition) {

    status.innerText =
        "❌ Səs tanıma dəstəklənmir.";

    return;

}


/* =========================================================
   VARIABLES
========================================================= */

let recognition = null;

let running = false;

let mode = "wake";

let restarting = false;

let commandTimer = null;


/* =========================================================
   WAKE WORDS
========================================================= */

const wakeWords = [

    "hey jarvis",
    "hey, jarvis",
    "hey jervis",
    "hey cervis",
    "hey carvis",
    "ey jarvis",
    "jarvis"

];


/* =========================================================
   NORMALIZE
========================================================= */

function normalize(text) {

    return text
        .toLowerCase()
        .replace(/[.,!?;:]/g, "")
        .replace(/\s+/g, " ")
        .trim();

}


/* =========================================================
   UI
========================================================= */

function wakeUI() {

    status.innerText =
        '👂 "Hey Jarvis" gözlənilir...';

    dot.style.background =
        "#ff3333";

    dot.style.boxShadow =
        "0 0 20px #ff3333";

}


function listeningUI() {

    status.innerText =
        "🎤 Sizi dinləyirəm...";

    dot.style.background =
        "#00ffd5";

    dot.style.boxShadow =
        "0 0 35px #00ffd5";

}


function thinkingUI() {

    status.innerText =
        "🧠 Düşünürəm...";

    dot.style.background =
        "#4285ff";

    dot.style.boxShadow =
        "0 0 35px #4285ff";

}


/* =========================================================
   CHECK WAKE WORD
========================================================= */

function hasWakeWord(text) {

    const clean = normalize(text);

    for (
        const word of wakeWords
    ) {

        if (
            clean.includes(
                normalize(word)
            )
        ) {

            return true;

        }

    }

    return false;

}


/* =========================================================
   REMOVE WAKE WORD
========================================================= */

function removeWakeWord(text) {

    let result = normalize(text);

    for (
        const word of wakeWords
    ) {

        result =
            result.replace(
                normalize(word),
                ""
            );

    }

    return result.trim();

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


    const preferred = [

        "Microsoft David",
        "Microsoft Mark",
        "Microsoft George",
        "Google US English",
        "David",
        "Mark",
        "George",
        "Daniel",
        "Thomas",
        "Arthur",
        "Alex",
        "Fred"

    ];


    for (
        const preferredName
        of preferred
    ) {

        const found =
            voices.find(
                v =>
                    v.name
                    .toLowerCase()
                    .includes(
                        preferredName
                        .toLowerCase()
                    )
            );

        if (found) {
            return found;
        }

    }


    /* AZƏRBAYCAN SƏSİ */

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


    /* ENGLISH FALLBACK */

    const english =
        voices.find(
            v =>
                v.lang &&
                v.lang
                .toLowerCase()
                .startsWith("en")
        );

    if (english) {
        return english;
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
        utterance.voice = voice;
    }


    /*
       Azərbaycan dili.
       Səs cihazdan seçilir.
    */

    utterance.lang = "az-AZ";


    /*
       Jarvis effekti
    */

    utterance.rate = 0.90;

    utterance.pitch = 0.75;

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
   SEND TO STREAMLIT
========================================================= */

function sendToStreamlit(text) {

    if (!text) {

        mode = "wake";

        restart();

        return;

    }


    thinkingUI();


    const parent =
        window.parent.document;


    /*
       Streamlit input-u tapılır.
    */

    const inputs =
        Array.from(
            parent.querySelectorAll(
                "input"
            )
        );


    let input = null;


    for (
        const element
        of inputs
    ) {

        const placeholder =
            (
                element
                .getAttribute(
                    "placeholder"
                ) || ""
            ).toLowerCase();


        const aria =
            (
                element
                .getAttribute(
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

            input = element;

            break;

        }

    }


    /*
       Əgər input tapılmadısa,
       bütün text input-lardan istifadə et.
    */

    if (!input) {

        input =
            inputs.find(
                el =>
                    el.type === "text"
            );

    }


    if (!input) {

        status.innerText =
            "⚠️ Mətn sahəsi tapılmadı.";

        mode = "wake";

        restart();

        return;

    }


    /*
       React / Streamlit üçün
       native setter
    */

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


    input.dispatchEvent(
        new Event(
            "change",
            {
                bubbles: true
            }
        )
    );


    /*
       Formu tap
    */

    setTimeout(
        function () {

            const form =
                input.closest("form");


            if (form) {

                const button =
                    form.querySelector(
                        'button[type="submit"]'
                    );


                if (button) {

                    button.click();

                    return;

                }

            }


            /*
               Fallback:
               Enter göndər
            */

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

        },
        250
    );


    /*
       Bir müddət sonra wake mode
    */

    setTimeout(
        function () {

            mode = "wake";

            restart();

        },
        1800
    );

}


/* =========================================================
   CREATE RECOGNITION
========================================================= */

function createRecognition() {

    const r =
        new Recognition();


    /*
       Azərbaycan dili
    */

    r.lang = "az-AZ";


    /*
       Bəzi Android cihazlarda
       az-AZ zəif işləyə bilər.
       alternativ nəticələr alınır.
    */

    r.continuous = false;

    r.interimResults = false;

    r.maxAlternatives = 5;


    /* =====================================================
       START
    ===================================================== */

    r.onstart =
        function () {

            running = true;

            restarting = false;


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


            /*
               Alternativ nəticələri yoxla
            */

            for (
                let i = 0;
                i <
                event.results[0].length;
                i++
            ) {

                const alternative =
                    normalize(
                        event.results[0][i]
                            .transcript
                    );


                if (
                    alternative
                ) {

                    bestText =
                        alternative;

                }


                /*
                   Wake mode-da Jarvis
                   sözünü tapdıqsa dərhal istifadə et
                */

                if (
                    mode === "wake" &&
                    hasWakeWord(
                        alternative
                    )
                ) {

                    bestText =
                        alternative;

                    break;

                }

            }


            console.log(
                "Jarvis eşitdi:",
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

                    restart();

                    return;

                }


                /*
                   Jarvis aktivləşdi
                */

                mode = "command";


                /*
                   Əgər istifadəçi
                   "Hey Jarvis, hava necədir?"
                   deyibsə, ayrıca ikinci
                   dinləməyə ehtiyac yoxdur.
                */

                const remaining =
                    removeWakeWord(
                        bestText
                    );


                if (remaining) {

                    sendToStreamlit(
                        remaining
                    );

                    return;

                }


                /*
                   Sadəcə "Hey Jarvis"
                   deyilibsə
                */

                status.innerText =
                    "🤖 Bəli cənab...";


                dot.style.background =
                    "#00ffd5";


                dot.style.boxShadow =
                    "0 0 40px #00ffd5";


                speak(
                    "Bəli cənab, xidmətinizdəyəm.",
                    function () {

                        mode =
                            "command";


                        setTimeout(
                            function () {

                                start();

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

                    restart();

                    return;

                }


                sendToStreamlit(
                    bestText
                );

                return;

            }

        };


    /* =====================================================
       ERROR
    ===================================================== */

    r.onerror =
        function (event) {

            console.log(
                "Recognition error:",
                event.error
            );


            running = false;


            if (
                event.error ===
                "not-allowed"
            ) {

                status.innerText =
                    "❌ Mikrofon icazəsi yoxdur.";

                dot.style.background =
                    "#ff0000";

                return;

            }


            if (
                event.error ===
                "service-not-allowed"
            ) {

                status.innerText =
                    "❌ Brauzer səs xidmətinə icazə vermir.";

                return;

            }


            if (
                event.error ===
                "audio-capture"
            ) {

                status.innerText =
                    "❌ Mikrofon tapılmadı.";

                return;

            }


            if (
                mode === "wake"
            ) {

                restart();

            }

        };


    /* =====================================================
       END
    ===================================================== */

    r.onend =
        function () {

            running = false;


            if (
                mode === "wake"
            ) {

                restart();

            }

        };


    return r;

}


/* =========================================================
   START
========================================================= */

function start() {

    if (running) {
        return;
    }


    try {

        recognition =
            createRecognition();


        recognition.start();

    }

    catch (error) {

        console.log(
            "Start error:",
            error
        );


        running = false;


        setTimeout(
            start,
            1200
        );

    }

}


/* =========================================================
   RESTART
========================================================= */

function restart() {

    if (restarting) {
        return;
    }


    restarting = true;


    if (recognition) {

        try {
            recognition.stop();
        }
        catch(e) {}

    }


    setTimeout(
        function () {

            restarting = false;

            mode = "wake";

            start();

        },
        700
    );

}


/* =========================================================
   LOAD VOICES
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

        status.innerText =
            '👂 "Hey Jarvis" gözlənilir...';

        start();

    },
    1000
);


})();

</script>

</body>

</html>
        """,
        height=270
    )


# ============================================================
# CHAT HISTORY
# ============================================================

st.markdown("---")


for idx, message in enumerate(
    st.session_state.messages
):

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
        placeholder="Məsələn: Bakı haqqında məlumat ver"
    )

    submit = st.form_submit_button(
        "➜ Göndər",
        use_container_width=True
    )


# ============================================================
# GEMINI
# ============================================================

if submit and prompt:

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


        for attempt in range(3):

            try:

                client =
                    get_gemini_client(attempt)


                response =
                    client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=
                                SYSTEM_INSTRUCTION,
                            temperature=0.2
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

                print(
                    "Gemini error:",
                    error
                )


                if attempt < 2:
                    time.sleep(2)


        if not response_text:

            response_text = (
                "Bağışlayın cənab, "
                "hazırda cavab ala bilmədim."
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

        clean_speech = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            response_text
        )


        clean_speech = re.sub(
            r"[*_#`]",
            "",
            clean_speech
        )


        speech_json = json.dumps(
            clean_speech,
            ensure_ascii=False
        )


        st.components.v1.html(
            f"""
<script>

(function() {{

    const text =
        {speech_json};


    if (
        !text ||
        !window.speechSynthesis
    ) {{
        return;
    }}


    function speak() {{

        window.speechSynthesis.cancel();


        const utterance =
            new SpeechSynthesisUtterance(
                text
            );


        const voices =
            window.speechSynthesis
                .getVoices();


        let selected = null;


        const preferred = [

            "Microsoft David",
            "Microsoft Mark",
            "Microsoft George",
            "David",
            "Mark",
            "George",
            "Daniel",
            "Thomas",
            "Arthur",
            "Alex"

        ];


        for (
            const wanted
            of preferred
        ) {{

            selected =
                voices.find(
                    v =>
                        v.name
                        .toLowerCase()
                        .includes(
                            wanted.toLowerCase()
                        )
                );


            if (selected) {{
                break;
            }}

        }}


        if (!selected) {{

            selected =
                voices.find(
                    v =>
                        v.lang &&
                        v.lang
                        .toLowerCase()
                        .startsWith("az")
                );

        }}


        if (!selected) {{

            selected =
                voices.find(
                    v =>
                        v.lang &&
                        v.lang
                        .toLowerCase()
                        .startsWith("en")
                );

        }}


        if (selected) {{
            utterance.voice = selected;
        }}


        utterance.lang = "az-AZ";

        utterance.rate = 0.90;

        utterance.pitch = 0.75;

        utterance.volume = 1.0;


        window.speechSynthesis
            .speak(utterance);

    }}


    const voices =
        window.speechSynthesis
            .getVoices();


    if (voices.length) {{

        speak();

    }} else {{

        window.speechSynthesis
            .onvoiceschanged =
            function() {{

                window.speechSynthesis
                    .onvoiceschanged = null;

                speak();

            }};

    }}

}})();

</script>
""",
            height=1
    )
