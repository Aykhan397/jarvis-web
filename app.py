import streamlit as st
from google import genai
from google.genai import types
import json
import re
import time


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="JARVIS AI",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
Sən JARVIS adlı şəxsi süni intellekt köməkçisisən.

İstifadəçi ilə əsasən Azərbaycan dilində danış.

Üslubun:
- ağıllı
- nəzakətli
- sürətli
- konkret
- təbii

Cavabları lazımsız yerə uzatma.
Sadə suallara qısa və aydın cavab ver.

İstifadəçi sənə "cənab" deyə müraciət edə bilər.
Uyğun olduqda sən də "cənab" deyə müraciət edə bilərsən.

Özünü JARVIS kimi apar.
"""


# ============================================================
# API KEY
# ============================================================

def get_api_keys():

    keys = []

    key1 = st.secrets.get("GEMINI_API_KEY_1")
    key2 = st.secrets.get("GEMINI_API_KEY_2")
    key_default = st.secrets.get("GEMINI_API_KEY")

    if key1:
        keys.append(key1)

    if key2 and key2 not in keys:
        keys.append(key2)

    if key_default and key_default not in keys:
        keys.append(key_default)

    return keys


def get_client(index=0):

    keys = get_api_keys()

    if not keys:
        raise ValueError(
            "Gemini API key tapılmadı. "
            "Secrets bölməsinə GEMINI_API_KEY əlavə edin."
        )

    return genai.Client(
        api_key=keys[index % len(keys)]
    )


# ============================================================
# SESSION
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice_started" not in st.session_state:
    st.session_state.voice_started = False


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.jarvis-header {
    text-align: center;
    padding: 15px;
}

.jarvis-header h1 {
    font-size: 44px;
    margin: 0;
    letter-spacing: 4px;
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

    questions = [
        m for m in st.session_state.messages
        if m["role"] == "user"
    ]

    if questions:

        for message in questions:

            text = message["content"]

            if len(text) > 45:
                text = text[:45] + "..."

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

    padding: 28px 20px;

    border-radius: 24px;

    background:
        radial-gradient(
            circle at center,
            #123030,
            #070707 70%
        );

    border: 1px solid #00ffd5;

    color: white;

    text-align: center;

    box-shadow:
        0 0 30px
        rgba(0,255,213,0.15);
}

.robot {
    font-size: 55px;
}

.title {

    margin-top: 8px;

    font-size: 30px;

    font-weight: bold;

    letter-spacing: 5px;

    color: #00ffd5;
}

.status {

    margin-top: 10px;

    color: #aaa;

    min-height: 22px;
}

.dot {

    width: 22px;

    height: 22px;

    border-radius: 50%;

    margin: 20px auto 5px;

    background: #ff3333;

    box-shadow:
        0 0 22px #ff3333;
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

    <div class="robot">🤖</div>

    <div class="title">JARVIS</div>

    <div id="status" class="status">
        Başlayır...
    </div>

    <div id="dot" class="dot"></div>

    <div class="hint">
        "Hey Jarvis" deyin
    </div>

</div>


<script>

(function () {

"use strict";


const status =
    document.getElementById("status");

const dot =
    document.getElementById("dot");


const Recognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;


if (!Recognition) {

    status.innerText =
        "❌ Bu brauzerdə səs tanıma yoxdur.";

    return;
}


let recognition = null;

let running = false;

let restarting = false;

let mode = "wake";

let restartTimer = null;


const wakeWords = [
    "hey jarvis",
    "hey jervis",
    "hey cervis",
    "hey carvis",
    "ey jarvis",
    "jarvis"
];


function normalize(text) {

    return String(text || "")
        .toLowerCase()
        .replace(/[.,!?;:()[\\]{}]/g, " ")
        .replace(/\\s+/g, " ")
        .trim();
}


function hasWakeWord(text) {

    const clean = normalize(text);

    return wakeWords.some(
        word => clean.includes(normalize(word))
    );
}


function removeWakeWord(text) {

    let result = normalize(text);

    wakeWords.forEach(function(word) {

        result = result.replace(
            normalize(word),
            " "
        );

    });

    return result
        .replace(/\\s+/g, " ")
        .trim();
}


function wakeUI() {

    status.innerText =
        '👂 "Hey Jarvis" gözlənilir...';

    dot.style.background = "#ff3333";

    dot.style.boxShadow =
        "0 0 25px #ff3333";
}


function listeningUI() {

    status.innerText =
        "🎤 Sizi dinləyirəm...";

    dot.style.background =
        "#00ffd5";

    dot.style.boxShadow =
        "0 0 40px #00ffd5";
}


function thinkingUI() {

    status.innerText =
        "🧠 Düşünürəm...";

    dot.style.background =
        "#4285ff";

    dot.style.boxShadow =
        "0 0 40px #4285ff";
}


function getVoice() {

    if (!window.speechSynthesis) {
        return null;
    }

    const voices =
        window.speechSynthesis.getVoices();

    if (!voices.length) {
        return null;
    }


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


    for (const wanted of preferred) {

        const found = voices.find(
            v =>
                v.name
                .toLowerCase()
                .includes(wanted.toLowerCase())
        );

        if (found) {
            return found;
        }
    }


    const azVoice = voices.find(
        v =>
            v.lang &&
            v.lang
                .toLowerCase()
                .startsWith("az")
    );

    if (azVoice) {
        return azVoice;
    }


    const english = voices.find(
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


function speak(text, callback) {

    if (!window.speechSynthesis) {

        if (callback) {
            callback();
        }

        return;
    }


    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(text);


    const voice = getVoice();


    if (voice) {
        utterance.voice = voice;
    }


    utterance.lang = "az-AZ";

    utterance.rate = 0.88;

    utterance.pitch = 0.72;

    utterance.volume = 1.0;


    utterance.onend = function() {

        if (callback) {
            callback();
        }

    };


    utterance.onerror = function() {

        if (callback) {
            callback();
        }

    };


    window.speechSynthesis.speak(
        utterance
    );
}


function findInput() {

    const parent =
        window.parent.document;


    const inputs =
        Array.from(
            parent.querySelectorAll("input")
        );


    for (const input of inputs) {

        const placeholder =
            (
                input.getAttribute("placeholder")
                || ""
            ).toLowerCase();


        const aria =
            (
                input.getAttribute("aria-label")
                || ""
            ).toLowerCase();


        if (
            placeholder.includes("jarvis") ||
            aria.includes("jarvis")
        ) {

            return input;
        }
    }


    return inputs.find(
        input => input.type === "text"
    ) || null;
}


function sendToStreamlit(text) {

    text = normalize(text);


    if (!text) {

        mode = "wake";

        restartRecognition();

        return;
    }


    thinkingUI();


    const input = findInput();


    if (!input) {

        status.innerText =
            "⚠️ Mətn sahəsi tapılmadı.";

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
            text
        );


        input.dispatchEvent(
            new Event(
                "input",
                { bubbles: true }
            )
        );


        input.dispatchEvent(
            new Event(
                "change",
                { bubbles: true }
            )
        );


        setTimeout(function() {

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

        }, 300);


        mode = "wake";


        setTimeout(function() {

            restartRecognition();

        }, 1800);


    } catch (error) {

        console.log(error);

        mode = "wake";

        restartRecognition();
    }
}


function createRecognition() {

    const r =
        new Recognition();


    r.lang = "az-AZ";

    r.continuous = false;

    r.interimResults = false;

    r.maxAlternatives = 5;


    r.onstart = function() {

        running = true;

        restarting = false;


        if (mode === "wake") {
            wakeUI();
        } else {
            listeningUI();
        }
    };


    r.onresult = function(event) {

        running = false;


        let text = "";


        const result =
            event.results[
                event.results.length - 1
            ];


        for (
            let i = 0;
            i < result.length;
            i++
        ) {

            const candidate =
                normalize(
                    result[i].transcript
                );


            if (!candidate) {
                continue;
            }


            if (!text) {
                text = candidate;
            }


            if (
                mode === "wake" &&
                hasWakeWord(candidate)
            ) {

                text = candidate;

                break;
            }
        }


        console.log(
            "JARVIS:",
            text
        );


        if (mode === "wake") {

            if (!hasWakeWord(text)) {

                restartRecognition();

                return;
            }


            mode = "command";


            const command =
                removeWakeWord(text);


            if (command) {

                sendToStreamlit(command);

                return;
            }


            status.innerText =
                "🤖 Bəli cənab...";


            dot.style.background =
                "#00ffd5";


            speak(
                "Bəli cənab, xidmətinizdəyəm.",
                function() {

                    mode = "command";

                    setTimeout(
                        startRecognition,
                        300
                    );

                }
            );


            return;
        }


        if (mode === "command") {

            if (!text) {

                mode = "wake";

                restartRecognition();

                return;
            }


            sendToStreamlit(text);
        }
    };


    r.onerror = function(event) {

        console.log(
            "Speech error:",
            event.error
        );


        running = false;

        restarting = false;


        if (
            event.error === "not-allowed"
        ) {

            status.innerText =
                "❌ Mikrofon icazəsi verilməyib.";

            dot.style.background =
                "#ff0000";

            return;
        }


        if (
            event.error === "audio-capture"
        ) {

            status.innerText =
                "❌ Mikrofon tapılmadı.";

            return;
        }


        if (
            event.error === "service-not-allowed"
        ) {

            status.innerText =
                "❌ Səs xidməti əlçatan deyil.";

            return;
        }


        restartRecognition();
    };


    r.onend = function() {

        running = false;

        restarting = false;


        if (mode === "wake") {
            restartRecognition();
        }
    };


    return r;
}


function startRecognition() {

    if (
        running ||
        restarting
    ) {
        return;
    }


    try {

        recognition =
            createRecognition();


        recognition.start();


    } catch (error) {

        console.log(error);

        running = false;


        clearTimeout(
            restartTimer
        );


        restartTimer =
            setTimeout(
                startRecognition,
                1000
            );
    }
}


function restartRecognition() {

    if (restarting) {
        return;
    }


    restarting = true;


    clearTimeout(
        restartTimer
    );


    if (recognition) {

        try {
            recognition.stop();
        } catch (e) {}
    }


    running = false;


    restartTimer =
        setTimeout(
            function() {

                restarting = false;

                mode = "wake";

                startRecognition();

            },
            700
        );
}


if (window.speechSynthesis) {

    window.speechSynthesis.getVoices();

}


setTimeout(function() {

    wakeUI();

    startRecognition();

}, 1000);


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
        placeholder="Məsələn: Bakı haqqında məlumat ver"
    )

    submit = st.form_submit_button(
        "➜ Göndər",
        use_container_width=True
    )


# ============================================================
# GEMINI RESPONSE
# ============================================================

if submit and prompt.strip():

    prompt = prompt.strip()


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


        # ====================================================
        # CONVERSATION
        # ====================================================

        contents = []


        for message in st.session_state.messages:

            role = message["role"]

            text = message["content"]


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
        # TRY GEMINI
        # ====================================================

        last_error = None


        for attempt in range(4):

            try:

                client =
                    get_client(attempt)

                response =
                    client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_INSTRUCTION,
                            temperature=0.25,
                            max_output_tokens=1200
                        )
                    )


                if response and response.text:

                    response_text =
                        response.text.strip()

                    break


            except Exception as error:

                last_error = str(error)

                print(
                    "Gemini error:",
                    error
                )


                if attempt < 3:
                    time.sleep(1.5)


        # ====================================================
        # FALLBACK
        # ====================================================

        if not response_text:

            response_text = (
                "Bağışlayın cənab, "
                "hazırda cavab ala bilmədim."
            )


        # ====================================================
        # SHOW
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
        # CLEAN SPEECH
        # ====================================================

        clean_speech = response_text


        clean_speech = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            clean_speech
        )


        clean_speech = re.sub(
            r"```[\s\S]*?```",
            "",
            clean_speech
        )


        clean_speech = re.sub(
            r"[*_#>`~]",
            "",
            clean_speech
        )


        clean_speech = re.sub(
            r"\s+",
            " ",
            clean_speech
        ).strip()


        speech_json = json.dumps(
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

const text = {speech_json};


if (
    !text ||
    !window.speechSynthesis
) {{
    return;
}}


function getVoice() {{

    const voices =
        window.speechSynthesis.getVoices();


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


    for (const wanted of preferred) {{

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


    const en =
        voices.find(
            v =>
                v.lang &&
                v.lang
                    .toLowerCase()
                    .startsWith("en")
        );


    if (en) {{
        return en;
    }}


    return voices[0] || null;
}}


function speak() {{

    window.speechSynthesis.cancel();


    const utterance =
        new SpeechSynthesisUtterance(text);


    const voice = getVoice();


    if (voice) {{
        utterance.voice = voice;
    }}


    utterance.lang = "az-AZ";

    utterance.rate = 0.88;

    utterance.pitch = 0.72;

    utterance.volume = 1.0;


    window.speechSynthesis.speak(
        utterance
    );
}}


const voices =
    window.speechSynthesis.getVoices();


if (voices.length) {{

    setTimeout(
        speak,
        150
    );

}} else {{

    window.speechSynthesis.onvoiceschanged =
        function() {{

            window.speechSynthesis.onvoiceschanged =
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
            height=1
            )
