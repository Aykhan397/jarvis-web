import os
import re
import json
import time

import streamlit as st
from google import genai


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Jarvis AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = "gemini-3.7-flash"

SYSTEM_PROMPT = """
Sən JARVIS adlı ağıllı şəxsi AI köməkçisisən.

İstifadəçi ilə əsasən Azərbaycan dilində danış.
Cavabların:
- ağıllı
- qısa
- aydın
- nəzakətli
- təbii olsun.

Özünü JARVIS kimi təqdim et.
Lazım olduqda Azərbaycan, Türk və İngilis dillərində cavab verə bilərsən.

İstifadəçi "Jarvis" deyə müraciət etdikdə bunun sənə müraciət olduğunu başa düş.
"""


# ============================================================
# API KEY
# ============================================================

def get_api_keys():
    keys = []

    for name in (
        "GEMINI_API_KEY_1",
        "GEMINI_API_KEY_2",
        "GEMINI_API_KEY",
    ):
        value = os.getenv(name)

        if value and value.strip():
            if value.strip() not in keys:
                keys.append(value.strip())

    try:
        for name in (
            "GEMINI_API_KEY_1",
            "GEMINI_API_KEY_2",
            "GEMINI_API_KEY",
        ):
            if name in st.secrets:
                value = str(st.secrets[name]).strip()

                if value and value not in keys:
                    keys.append(value)
    except Exception:
        pass

    return keys


API_KEYS = get_api_keys()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "api_index" not in st.session_state:
    st.session_state.api_index = 0

if "last_voice_command" not in st.session_state:
    st.session_state.last_voice_command = ""

if "voice_enabled" not in st.session_state:
    st.session_state.voice_enabled = True


# ============================================================
# GEMINI
# ============================================================

def create_client(api_key):
    return genai.Client(api_key=api_key)


def ask_jarvis(user_text):
    if not API_KEYS:
        return (
            "⚠️ Gemini API açarı tapılmadı.\n\n"
            "GEMINI_API_KEY dəyişənini əlavə et."
        )

    history = []

    for message in st.session_state.messages[-20:]:
        role = message.get("role", "user")
        content = message.get("content", "")

        if role == "assistant":
            role = "model"

        history.append(
            {
                "role": role,
                "parts": [{"text": content}],
            }
        )

    history.append(
        {
            "role": "user",
            "parts": [{"text": user_text}],
        }
    )

    last_error = None

    for attempt in range(len(API_KEYS)):
        index = (
            st.session_state.api_index + attempt
        ) % len(API_KEYS)

        try:
            client = create_client(API_KEYS[index])

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config={
                    "system_instruction": SYSTEM_PROMPT,
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                },
            )

            text = getattr(response, "text", None)

            if text:
                st.session_state.api_index = index
                return text.strip()

            last_error = "Gemini boş cavab qaytardı."

        except Exception as error:
            last_error = error

            if len(API_KEYS) > 1:
                time.sleep(0.5)

    return f"⚠️ JARVIS xətası:\n\n{last_error}"


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    text = text.lower().strip()

    replacements = {
        "ə": "e",
        "ı": "i",
        "ö": "o",
        "ü": "u",
        "ş": "s",
        "ç": "c",
        "ğ": "g",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"\s+", " ", text)

    return text


# ============================================================
# VOICE UI
# ============================================================

VOICE_HTML = r"""
<div id="jarvisVoiceBox">

<style>
#jarvisVoiceBox {
    width: 100%;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(120,120,120,.25);
    background: rgba(30,30,30,.45);
    font-family: Arial, sans-serif;
}

#jarvisStatus {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 12px;
}

#jarvisText {
    width: 100%;
    box-sizing: border-box;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid rgba(150,150,150,.3);
    background: rgba(0,0,0,.2);
    color: inherit;
    outline: none;
}

.jarvisButtons {
    display: flex;
    gap: 10px;
    margin-top: 12px;
    flex-wrap: wrap;
}

.jarvisBtn {
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    cursor: pointer;
    font-weight: 600;
}

#startBtn {
    background: #2196f3;
    color: white;
}

#stopBtn {
    background: #555;
    color: white;
}

#sendBtn {
    background: #4caf50;
    color: white;
}
</style>


<div id="jarvisStatus">
🎙️ Jarvis hazırdır
</div>

<input
    id="jarvisText"
    type="text"
    placeholder="Danış və ya əmri buraya yaz..."
/>

<div class="jarvisButtons">
    <button class="jarvisBtn" id="startBtn">
        🎙️ Dinlə
    </button>

    <button class="jarvisBtn" id="stopBtn">
        ⏹️ Dayandır
    </button>

    <button class="jarvisBtn" id="sendBtn">
        ➤ Göndər
    </button>
</div>


<script>

(function () {

    const status = document.getElementById("jarvisStatus");
    const input = document.getElementById("jarvisText");

    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const sendBtn = document.getElementById("sendBtn");

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    let recognition = null;
    let listening = false;
    let wakeMode = true;

    const wakeWords = [
        "hey jarvis",
        "hey jervis",
        "hey cervis",
        "hey carvis",
        "ey jarvis",
        "jarvis"
    ];


    function setStatus(text) {
        status.textContent = text;
    }


    function cleanText(text) {
        return text
            .toLowerCase()
            .replace(/[.,!?;:]/g, " ")
            .replace(/\s+/g, " ")
            .trim();
    }


    function findWakeWord(text) {

        const normalized = cleanText(text);

        for (const word of wakeWords) {

            if (normalized.includes(word)) {
                return word;
            }
        }

        return null;
    }


    function removeWakeWord(text, wakeWord) {

        if (!wakeWord) {
            return text;
        }

        const regex = new RegExp(
            wakeWord.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
            "i"
        );

        return text
            .replace(regex, "")
            .replace(/\s+/g, " ")
            .trim();
    }


    function sendToStreamlit(text) {

        text = text.trim();

        if (!text) {
            return;
        }

        input.value = text;

        input.dispatchEvent(
            new Event("input", {
                bubbles: true
            })
        );

        input.dispatchEvent(
            new Event("change", {
                bubbles: true
            })
        );

        const form = input.closest("form");

        if (form) {

            try {
                if (form.requestSubmit) {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            } catch (error) {
                console.log(error);
            }
        }
    }


    function processSpeech(text) {

        if (!text) {
            return;
        }

        const wakeWord = findWakeWord(text);

        if (wakeMode) {

            if (!wakeWord) {
                setStatus("👂 Jarvis oyanma sözünü gözləyir...");
                return;
            }

            const command =
                removeWakeWord(text, wakeWord);

            if (command) {
                sendToStreamlit(command);
                setStatus("⚡ Əmr qəbul edildi");
            } else {
                setStatus("🎙️ Bəli, sizi dinləyirəm...");
            }

            return;
        }

        sendToStreamlit(text);
    }


    function createRecognition() {

        if (!SpeechRecognition) {

            setStatus(
                "❌ Bu brauzer səs tanımanı dəstəkləmir."
            );

            return null;
        }

        const r = new SpeechRecognition();

        r.lang = "az-AZ";
        r.continuous = true;
        r.interimResults = false;
        r.maxAlternatives = 1;


        r.onstart = function () {

            listening = true;

            setStatus(
                "👂 Dinləyirəm... \"Hey Jarvis\" deyin."
            );
        };


        r.onresult = function (event) {

            for (
                let i = event.resultIndex;
                i < event.results.length;
                i++
            ) {

                if (!event.results[i].isFinal) {
                    continue;
                }

                const text =
                    event.results[i][0].transcript.trim();

                if (text) {
                    processSpeech(text);
                }
            }
        };


        r.onerror = function (event) {

            console.log(
                "Speech recognition error:",
                event.error
            );

            if (event.error === "not-allowed") {

                setStatus(
                    "⚠️ Mikrofon icazəsi verilməyib."
                );

                listening = false;
                return;
            }

            if (listening) {

                setTimeout(function () {

                    try {
                        r.start();
                    } catch (error) {
                        console.log(error);
                    }

                }, 1000);
            }
        };


        r.onend = function () {

            if (!listening) {
                return;
            }

            setTimeout(function () {

                try {
                    r.start();
                } catch (error) {
                    console.log(error);
                }

            }, 300);
        };


        return r;
    }


    startBtn.onclick = function () {

        if (!SpeechRecognition) {

            setStatus(
                "❌ Chrome kimi uyğun brauzerdən istifadə edin."
            );

            return;
        }

        if (!recognition) {
            recognition = createRecognition();
        }

        if (!recognition) {
            return;
        }

        listening = true;

        try {
            recognition.start();
        } catch (error) {
            console.log(error);
        }
    };


    stopBtn.onclick = function () {

        listening = false;

        if (recognition) {

            try {
                recognition.stop();
            } catch (error) {
                console.log(error);
            }
        }

        setStatus("⏹️ Dinləmə dayandırıldı.");
    };


    sendBtn.onclick = function () {

        const text = input.value.trim();

        if (text) {
            sendToStreamlit(text);
        }
    };


    input.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {

                event.preventDefault();

                const text =
                    input.value.trim();

                if (text) {
                    sendToStreamlit(text);
                }
            }
        }
    );

})();
</script>

</div>
"""


# ============================================================
# MALE VOICE TTS
# ============================================================

def speak_javascript(text):
    safe_text = json.dumps(text, ensure_ascii=False)

    html = f"""
    <script>
    (function() {{

        const text = {safe_text};

        if (!("speechSynthesis" in window)) {{
            return;
        }}

        window.speechSynthesis.cancel();

        const speak = () => {{

            const voices =
                window.speechSynthesis.getVoices();

            let selected = null;

            const maleNames = [
                "David",
                "Mark",
                "Daniel",
                "George",
                "James",
                "Alex",
                "Google UK English Male",
                "Microsoft David"
            ];

            for (const name of maleNames) {{

                selected = voices.find(
                    v => v.name
                        .toLowerCase()
                        .includes(name.toLowerCase())
                );

                if (selected) {{
                    break;
                }}
            }}

            if (!selected) {{

                selected = voices.find(
                    v =>
                        v.lang &&
                        v.lang.toLowerCase().startsWith("en")
                );
            }}

            const utterance =
                new SpeechSynthesisUtterance(text);

            if (selected) {{
                utterance.voice = selected;
            }}

            utterance.rate = 0.95;
            utterance.pitch = 0.85;
            utterance.volume = 1.0;

            window.speechSynthesis.speak(
                utterance
            );
        }};

        if (
            window.speechSynthesis
                .getVoices().length
        ) {{
            speak();
        }} else {{
            window.speechSynthesis.onvoiceschanged =
                speak;
        }}

    }})();
    </script>
    """

    st.components.v1.html(
        html,
        height=0,
    )


# ============================================================
# HEADER
# ============================================================

st.title("🤖 JARVIS AI")

st.caption(
    "Səsli AI köməkçisi • Azərbaycan dili • Gemini"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Jarvis")

    st.success(
        "🟢 Sistem hazırdır"
        if API_KEYS
        else "🔴 API açarı yoxdur"
    )

    st.session_state.voice_enabled = st.toggle(
        "🔊 Cavabı səsləndir",
        value=st.session_state.voice_enabled,
    )

    st.divider()

    st.markdown(
        """
        **Səsli istifadə:**

        1. 🎙️ **Dinlə** düyməsinə bas.
        2. **Hey Jarvis** de.
        3. Əmrini söylə.

        Məsələn:

        **“Hey Jarvis, mənə süni intellekt haqqında danış.”**
        """
    )

    if st.button(
        "🗑️ Söhbəti təmizlə",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()


# ============================================================
# VOICE CONTROL
# ============================================================

st.components.v1.html(
    VOICE_HTML,
    height=220,
    scrolling=False,
)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.messages:

    role = message["role"]

    with st.chat_message(
        "assistant" if role == "assistant" else "user"
    ):
        st.markdown(message["content"])


# ============================================================
# TEXT INPUT
# ============================================================

prompt = st.chat_input(
    "Jarvisə əmr ver..."
)


# ============================================================
# PROCESS MESSAGE
# ============================================================

if prompt:

    prompt = prompt.strip()

    if not prompt:
        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("JARVIS düşünür..."):

            answer = ask_jarvis(prompt)

        st.markdown(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    if (
        st.session_state.voice_enabled
        and answer
        and not answer.startswith("⚠️")
    ):
        speak_javascript(answer)
