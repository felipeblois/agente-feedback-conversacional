document.addEventListener("DOMContentLoaded", () => {
    if (!window.AppConfig) return;

    const token = window.AppConfig.publicToken;
    let responseId = null;

    const els = {
        messages: document.getElementById("chat-messages"),
        inputArea: document.getElementById("input-area"),
        scoreContainer: document.getElementById("score-input-container"),
        textContainer: document.getElementById("text-input-container"),
        textarea: document.getElementById("chat-textarea"),
        sendBtn: document.getElementById("send-btn"),
        scoreBtns: document.querySelectorAll(".score-btn"),
        startBtn: document.getElementById("start-chat-btn"),
        startContainer: document.getElementById("start-container"),
        participantName: document.getElementById("participant-name"),
    };

    function addMessage(text, type) {
        const div = document.createElement("div");
        div.className = `message ${type}-msg`;
        div.innerText = text;
        els.messages.appendChild(div);
        els.messages.scrollTop = els.messages.scrollHeight;
    }

    function showInput(type) {
        els.inputArea.style.display = "block";
        if (type === "score") {
            els.scoreContainer.style.display = "flex";
            els.textContainer.style.display = "none";
        } else if (type === "text") {
            els.scoreContainer.style.display = "none";
            els.textContainer.style.display = "flex";
            els.textarea.focus();
        } else {
            els.inputArea.style.display = "none";
        }
    }

    function handleNextQuestion(question) {
        if (!question) {
            addMessage(
                "Obrigado pelo seu tempo! Suas respostas nos ajudarão muito. Você pode fechar sua janela agora.",
                "system",
            );
            document.body.classList.add("conversation-complete");
            showInput("none");
            return;
        }

        setTimeout(() => {
            addMessage(question.text, "system");
            showInput(question.type);
        }, 420);
    }

    els.startBtn.addEventListener("click", async () => {
        const participantName = els.participantName ? els.participantName.value.trim() : "";
        const startPayload = participantName
            ? { anonymous: false, participant_name: participantName }
            : { anonymous: true };

        try {
            const res = await fetch(`/api/v1/public/${token}/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(startPayload),
            });
            const data = await res.json();

            els.startContainer.style.display = "none";
            responseId = data.response_id;
            handleNextQuestion(data.first_question);
        } catch (error) {
            console.error(error);
            addMessage("Erro ao iniciar conversa. Tente recarregar.", "system");
        }
    });

    els.scoreBtns.forEach((btn) => {
        btn.addEventListener("click", async (event) => {
            const score = parseInt(event.target.dataset.score, 10);
            addMessage(score.toString(), "user");
            showInput("none");

            try {
                const res = await fetch(`/api/v1/public/${token}/score`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ response_id: responseId, score }),
                });
                const data = await res.json();
                handleNextQuestion(data.next_question);
            } catch (error) {
                console.error(error);
            }
        });
    });

    els.sendBtn.addEventListener("click", async () => {
        const text = els.textarea.value.trim();
        if (!text) return;

        els.textarea.value = "";
        addMessage(text, "user");
        showInput("none");

        try {
            const res = await fetch(`/api/v1/public/${token}/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ response_id: responseId, message: text }),
            });
            const data = await res.json();

            if (data.conversation_finished) {
                handleNextQuestion(null);
            } else {
                handleNextQuestion(data.next_question);
            }
        } catch (error) {
            console.error(error);
        }
    });

    if (els.participantName) {
        els.participantName.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                els.startBtn.click();
            }
        });
    }
});
