document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chatWindow");
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const quickButtons = document.querySelectorAll(".quick-question");

    let isWaitingForReply = false;

    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function autoResizeTextarea() {
        userInput.style.height = "auto";
        userInput.style.height = userInput.scrollHeight + "px";
    }

    function addMessage(text, sender = "bot", isTypingIndicator = false) {
        const msg = document.createElement("div");
        msg.classList.add("chat-message", sender);

        const bubble = document.createElement("div");
        bubble.classList.add("bubble");

        if (isTypingIndicator) {
            bubble.classList.add("typing-indicator");
            bubble.innerHTML = `
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            `;
        } else {
            bubble.textContent = text;
        }

        const timestamp = document.createElement("div");
        timestamp.classList.add("timestamp");
        const now = new Date();
        timestamp.textContent = now.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
        });

        msg.appendChild(bubble);
        msg.appendChild(timestamp);
        chatWindow.appendChild(msg);
        scrollToBottom();

        return msg;
    }

    async function sendMessage(message) {
        if (!message || isWaitingForReply) return;
        isWaitingForReply = true;

        // Show user message
        addMessage(message, "user");

        // Typing indicator
        const typingMsg = addMessage("", "bot", true);

        // Disable input & button
        userInput.disabled = true;
        const sendBtn = chatForm.querySelector("button[type='submit']");
        if (sendBtn) sendBtn.disabled = true;

        try {
            const response = await fetch(`/get?msg=${encodeURIComponent(message)}`, {
                method: "GET",
            });

            const data = await response.json();

            // Remove typing indicator
            chatWindow.removeChild(typingMsg);

            const reply =
                data.response ||
                "I couldn't generate a response. Please try again or consult a qualified lawyer for detailed advice.";

            addMessage(reply, "bot");
        } catch (error) {
            console.error("Error calling /get:", error);
            try {
                chatWindow.removeChild(typingMsg);
            } catch (e) {
                /* ignore */
            }
            addMessage(
                "Something went wrong while contacting the legal assistant. Please try again. For urgent legal matters, contact a licensed lawyer immediately.",
                "bot"
            );
        } finally {
            isWaitingForReply = false;
            userInput.disabled = false;
            const sendBtn2 = chatForm.querySelector("button[type='submit']");
            if (sendBtn2) sendBtn2.disabled = false;
            userInput.focus();
        }
    }

    // Form submit
    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;
        userInput.value = "";
        autoResizeTextarea();
        sendMessage(text);
    });

    // Enter to send, Shift+Enter for newline
    userInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;
            userInput.value = "";
            autoResizeTextarea();
            sendMessage(text);
        }
    });

    // Auto resize textarea
    userInput.addEventListener("input", autoResizeTextarea);
    autoResizeTextarea();

    // Quick question chips
    quickButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const question = btn.textContent.trim();
            if (!question) return;
            sendMessage(question);
        });
    });

    // Focus on load
    userInput.focus();
});
