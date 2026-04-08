document.addEventListener("DOMContentLoaded", () => {
    if (!window.AppConfig) return; // Not on chat page

    const token = window.AppConfig.publicToken;
    let responseId = null;

    const els = {
        messages: document.getElementById('chat-messages'),
        inputArea: document.getElementById('input-area'),
        scoreContainer: document.getElementById('score-input-container'),
        textContainer: document.getElementById('text-input-container'),
        textarea: document.getElementById('chat-textarea'),
        sendBtn: document.getElementById('send-btn'),
        scoreBtns: document.querySelectorAll('.score-btn'),
        startBtn: document.getElementById('start-chat-btn'),
        startContainer: document.getElementById('start-container')
    };

    function addMessage(text, type) {
        const div = document.createElement('div');
        div.className = `message ${type}-msg`;
        div.innerText = text;
        els.messages.appendChild(div);
        els.messages.scrollTop = els.messages.scrollHeight;
    }

    function showInput(type) {
        els.inputArea.style.display = 'block';
        if (type === 'score') {
            els.scoreContainer.style.display = 'flex';
            els.textContainer.style.display = 'none';
        } else if (type === 'text') {
            els.scoreContainer.style.display = 'none';
            els.textContainer.style.display = 'flex';
            els.textarea.focus();
        } else {
            els.inputArea.style.display = 'none';
        }
    }

    async function handleNextQuestion(q) {
        if (!q) {
            addMessage("Obrigado pelo seu tempo! Suas respostas nos ajudarão muito.", "system");
            showInput('none');
            return;
        }
        
        setTimeout(() => {
            addMessage(q.text, "system");
            showInput(q.type);
        }, 500);
    }

    els.startBtn.addEventListener('click', async () => {
        els.startContainer.style.display = 'none';
        
        try {
            const res = await fetch(`/api/v1/public/${token}/start`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ anonymous: true })
            });
            const data = await res.json();
            
            responseId = data.response_id;
            handleNextQuestion(data.first_question);
        } catch (e) {
            console.error(e);
            addMessage("Erro ao iniciar conversa. Tente recarregar.", "system");
        }
    });

    els.scoreBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const score = parseInt(e.target.dataset.score);
            addMessage(score.toString(), "user");
            showInput('none');

            try {
                const res = await fetch(`/api/v1/public/${token}/score`, {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ response_id: responseId, score: score })
                });
                const data = await res.json();
                handleNextQuestion(data.next_question);
            } catch (e) { console.error(e); }
        });
    });

    els.sendBtn.addEventListener('click', async () => {
        const text = els.textarea.value.trim();
        if (!text) return;
        
        els.textarea.value = '';
        addMessage(text, "user");
        showInput('none');

        try {
            const res = await fetch(`/api/v1/public/${token}/message`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ response_id: responseId, message: text })
            });
            const data = await res.json();
            
            if (data.conversation_finished) {
                handleNextQuestion(null);
            } else {
                handleNextQuestion(data.next_question);
            }
        } catch (e) { console.error(e); }
    });
});
