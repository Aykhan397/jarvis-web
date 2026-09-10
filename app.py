from flask import Flask, render_template_string, request, jsonify
from google import genai

app = Flask(__name__)

# Google GenAI müştərisini təyin edirik (API açarını bura daxil etməlisən)
client = genai.Client(api_key="SƏNİN_GEMİNİ_APİ_AÇARIN")

# 4 funksiyanı özündə birləşdirən vahid Jarvis interfeysi
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>Jarvis - AI İdarəetmə Paneli</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; display: flex; height: 100vh; }
        .sidebar { width: 260px; background: #1e293b; padding: 20px; display: flex; flex-direction: column; border-right: 1px solid #334155; }
        .sidebar h2 { color: #38bdf8; font-size: 22px; margin-bottom: 20px; text-align: center; }
        .nav-btn { background: #334155; color: #f8fafc; border: none; padding: 12px; margin-bottom: 10px; border-radius: 8px; cursor: pointer; text-align: left; font-size: 14px; transition: 0.3s; }
        .nav-btn:hover, .nav-btn.active { background: #0ea5e9; color: white; }
        
        .main-content { flex: 1; display: flex; flex-direction: column; padding: 20px; overflow: hidden; }
        .panel { display: none; flex: 1; flex-direction: column; height: 100%; }
        .panel.active { display: flex; }
        
        .chat-box { flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; overflow-y: auto; margin-bottom: 15px; }
        .message { margin-bottom: 12px; line-height: 1.5; }
        .user { color: #4ade80; }
        .jarvis { color: #38bdf8; }
        
        .input-group { display: flex; gap: 10px; }
        textarea, input[type="text"] { flex: 1; background: #1e293b; border: 1px solid #334155; color: white; padding: 12px; border-radius: 8px; resize: none; font-family: inherit; }
        button.send-btn { background: #0ea5e9; color: white; border: none; padding: 0 20px; border-radius: 8px; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button.send-btn:hover { background: #0284c7; }
        
        .card { background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px; }
        pre { background: #090d16; padding: 15px; border-radius: 6px; overflow-x: auto; color: #38bdf8; }
    </style>
</head>
<body>

    <div class="sidebar">
        <h2>JARVIS v1.0</h2>
        <button class="nav-btn active" onclick="switchTab(0)">1. Söhbət (Chat)</button>
        <button class="nav-btn" onclick="switchTab(1)">2. Sürətli Sual</button>
        <button class="nav-btn" onclick="switchTab(2)">3. Kod Köməkçisi</button>
        <button class="nav-btn" onclick="switchTab(3)">4. Məsləhətçi Rejimi</button>
    </div>

    <div class="main-content">
        <!-- 1. Söhbət Paneli -->
        <div class="panel active" id="panel-0">
            <h3>Söhbət Rejimi</h3>
            <div class="chat-box" id="chatBox-0"></div>
            <div class="input-group">
                <input type="text" id="input-0" placeholder="Jarvis ilə söhbət et..." onkeypress="if(event.key === 'Enter') sendData(0)">
                <button class="send-btn" onclick="sendData(0)">Göndər</button>
            </div>
        </div>

        <!-- 2. Sürətli Sual Paneli -->
        <div class="panel" id="panel-1">
            <h3>Sürətli Sual-Cavab</h3>
            <div class="card">
                <p>İstənilən qısa sualı birbaşa soruş və sürətli cavab al.</p>
            </div>
            <div class="chat-box" id="chatBox-1"></div>
            <div class="input-group">
                <input type="text" id="input-1" placeholder="Məsələn: Kvant fizikası nədir?" onkeypress="if(event.key === 'Enter') sendData(1)">
                <button class="send-btn" onclick="sendData(1)">Sorğula</button>
            </div>
        </div>

        <!-- 3. Kod Köməkçisi Paneli -->
        <div class="panel" id="panel-2">
            <h3>Kodlaşdırma və Debug Köməkçisi</h3>
            <div class="chat-box" id="chatBox-2"></div>
            <div class="input-group">
                <textarea id="input-2" rows="2" placeholder="Hansı dildə və nə cür kod istəyirsən yaz..."></textarea>
                <button class="send-btn" onclick="sendData(2)">Kodu Yaz</button>
            </div>
        </div>

        <!-- 4. Məsləhətçi Paneli -->
        <div class="panel" id="panel-3">
            <h3>Strategiya və Planlaşdırma Məsləhətçisi</h3>
            <div class="chat-box" id="chatBox-3"></div>
            <div class="input-group">
                <input type="text" id="input-3" placeholder="Plan və ya strategiya qurmaq üçün mövzu yaz..." onkeypress="if(event.key === 'Enter') sendData(3)">
                <button class="send-btn" onclick="sendData(3)">Plan qur</button>
            </div>
        </div>
    </div>

    <script>
        function switchTab(index) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            document.getElementById('panel-' + index).classList.add('active');
            document.querySelectorAll('.nav-btn')[index].classList.add('active');
        }

        async function sendData(mode) {
            const inputEl = document.getElementById('input-' + mode);
            const chatBox = document.getElementById('chatBox-' + mode);
            const text = inputEl.value.trim();
            if (!text) return;

            chatBox.innerHTML += `<div class="message user"><b>Sən:</b> ${text}</div>`;
            inputEl.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/jarvis-process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, mode: mode })
                });
                const data = await response.json();
                chatBox.innerHTML += `<div class="message jarvis"><b>Jarvis:</b><br>${data.reply.replace(/\\n/g, '<br>')}</div>`;
            } catch (error) {
                chatBox.innerHTML += `<div class="message jarvis"><b>Jarvis:</b> Xəta baş verdi.</div>`;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/jarvis-process', methods=['POST'])
def jarvis_process():
    data = request.json
    user_message = data.get('message')
    mode = data.get('mode', 0)
    
    # Rejimlərə görə Jarvis-in sistem təlimatlarını (rolunu) tənzimləyirik
    system_prompts = [
        "Sən Jarvis-sən, dostcanlı və köməkçi süni intellekt köməkçisisən.",
        "Sən Jarvis-sən. Verilən suallara çox qısa, dəqiq və laktik cavablar ver.",
        "Sən peşəkar proqramlaşdırma mütəxəssisi Jarvis-sən. Təmiz, səliqəli kodlar və izahatlar yaz.",
        "Sən strateji planlaşdırma və məsləhətçi Jarvis-sən. İstifadəçiyə addım-addım planlar və məsləhətlər təqdim et."
    ]
    
    prompt = f"{system_prompts[int(mode)]}\n\nİstifadəçi: {user_message}"

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        reply = response.text
    except Exception as e:
        reply = f"Sistem xətası: {str(e)}"
    
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
