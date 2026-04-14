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
        website: document.getElementById("website"),
        consentCheckbox: document.getElementById("consent-checkbox"),
    };

    function addMessage(text, type) {
        const div = document.createElement("div");
        div.className = `message ${type}-msg`;
        div.innerText = text;
        els.messages.appendChild(div);
        els.messages.scrollTop = els.messages.scrollHeight;
    }

    function addThinkingMessage() {
        const div = document.createElement("div");
        div.className = "message system-msg";
        div.innerText = "Pensando na proxima pergunta...";
        div.dataset.thinking = "true";
        els.messages.appendChild(div);
        els.messages.scrollTop = els.messages.scrollHeight;
    }

    function removeThinkingMessage() {
        const thinking = els.messages.querySelector('[data-thinking="true"]');
        if (thinking) {
            thinking.remove();
        }
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
        removeThinkingMessage();
        if (!question) {
            addMessage(
                "Obrigado pelo seu tempo! Suas respostas nos ajudarao muito. Voce pode fechar sua janela agora.",
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
        const website = els.website ? els.website.value.trim() : "";
        const consentAccepted = Boolean(els.consentCheckbox && els.consentCheckbox.checked);

        if (!consentAccepted) {
            addMessage("Voce precisa concordar com o uso das respostas para iniciar o feedback.", "system");
            return;
        }

        const startPayload = participantName
            ? { anonymous: false, participant_name: participantName, consent_accepted: true, website }
            : { anonymous: true, consent_accepted: true, website };

        try {
            const res = await fetch(`/api/v1/public/${token}/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(startPayload),
            });
            if (!res.ok) {
                const errorPayload = await res.json().catch(() => ({}));
                throw new Error(errorPayload.detail || "Erro ao iniciar conversa.");
            }
            const data = await res.json();

            els.startContainer.style.display = "none";
            responseId = data.response_id;
            handleNextQuestion(data.first_question);
        } catch (error) {
            console.error(error);
            addMessage(error.message || "Erro ao iniciar conversa. Tente recarregar.", "system");
        }
    });

    els.scoreBtns.forEach((btn) => {
        btn.addEventListener("click", async (event) => {
            const score = parseInt(event.target.dataset.score, 10);
            addMessage(score.toString(), "user");
            showInput("none");
            addThinkingMessage();

            try {
                const res = await fetch(`/api/v1/public/${token}/score`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ response_id: responseId, score }),
                });
                const data = await res.json();

                if (data.conversation_finished) {
                    handleNextQuestion(null);
                } else {
                    handleNextQuestion(data.next_question);
                }
            } catch (error) {
                console.error(error);
                removeThinkingMessage();
                addMessage("Nao foi possivel continuar a conversa agora. Tente novamente em instantes.", "system");
                showInput("score");
            }
        });
    });

    els.sendBtn.addEventListener("click", async () => {
        const text = els.textarea.value.trim();
        if (!text) return;

        els.textarea.value = "";
        addMessage(text, "user");
        showInput("none");
        addThinkingMessage();

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
            removeThinkingMessage();
            addMessage("Houve uma falha temporaria ao gerar a proxima pergunta. Tente enviar novamente.", "system");
            showInput("text");
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
