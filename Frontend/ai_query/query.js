const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");
const sessionList = document.getElementById("sessionList");
const imageInput = document.getElementById("imageInput");

let currentSessionId = localStorage.getItem("current_session_id") || Date.now().toString();

window.onload = () => {
    const name = localStorage.getItem("farmer_username");
    if (name) {
        document.getElementById("farmerName").innerText = name;
    }

    loadSidebar();
    loadSessionHistory(currentSessionId);
};

function startNewChat() {
    currentSessionId = Date.now().toString();
    localStorage.setItem("current_session_id", currentSessionId);

    chatBox.innerHTML = `
        <div class="message ai">
            <img src="../assets/avatar.png" class="avatar">
            <div class="bubble">New session started. How can I help you with your crops today?</div>
        </div>`;

    loadSidebar();
}

async function loadSidebar() {
    const userId = localStorage.getItem("farmer_user_id") || 1;

    try {
        const response = await fetch(`http://127.0.0.1:8000/sessions/${userId}`);
        const data = await response.json();

        sessionList.innerHTML = "";

        data.sessions.forEach(s => {
            const div = document.createElement("div");
            div.className = `session-item ${s.session_id === currentSessionId ? 'active' : ''}`;
            div.innerText = s.title.length > 25 ? s.title.substring(0, 25) + "..." : s.title;
            div.onclick = () => loadSessionHistory(s.session_id);
            sessionList.appendChild(div);
        });

    } catch (err) {
        console.error("Sidebar load error:", err);
    }
}

async function loadSessionHistory(sid) {
    currentSessionId = sid;
    localStorage.setItem("current_session_id", sid);
    chatBox.innerHTML = "";

    try {
        const response = await fetch(`http://127.0.0.1:8000/history/${sid}`);
        const data = await response.json();

        if (data.history.length === 0) {
            startNewChat();
            return;
        }

        data.history.forEach(chat => {
            appendMessage("user", chat.user_query);
            appendMessage("ai", chat.ai_response);
        });

        loadSidebar();
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        console.error("History load error:", err);
    }
}

async function sendMessage(file = null) {
    const question = userInput.value.trim();
    const userId = localStorage.getItem("farmer_user_id") || 1;

    if (!question && !file) return;

    if (file) {
        appendMessage("user", "📸 Sent a leaf image for analysis...");
    } else {
        appendMessage("user", question);
    }

    userInput.value = "";
    appendMessage("ai", "", true);

    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("session_id", currentSessionId);
    if (question) formData.append("query", question);
    if (file) formData.append("file", file);

    try {
        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            body: formData
        });

        const loader = document.getElementById("ai-thinking");
        if (loader) loader.remove();

        const data = await response.json();

        let finalOutput = data.response;
        if (data.detected) {
            finalOutput = `<strong>Diagnosis:</strong> ${data.detected}<br><br>${data.response}`;
        }

        appendMessage("ai", finalOutput);
        loadSidebar();

    } catch (error) {
        console.error(error);
        appendMessage("ai", "Sorry, I couldn't connect to the farming assistant.");
    }
}

async function clearChat() {
    const userId = localStorage.getItem("farmer_user_id") || 1;

    if (!confirm("Are you sure? This will permanently delete all your chat history.")) return;

    try {
        const response = await fetch(`http://127.0.0.1:8000/clear/${userId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            startNewChat();
        }

    } catch (err) {
        console.error(err);
    }
}

function appendMessage(sender, text, isLoader = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);

    if (sender === "ai") {
        const avatar = document.createElement("img");
        avatar.src = "../assets/avatar.png";
        avatar.classList.add("avatar");
        messageDiv.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    if (isLoader) {
        bubble.innerHTML = "Thinking...";
        messageDiv.id = "ai-thinking";
    } else {
        bubble.innerHTML = text.replace(/\n/g, "<br>");
    }

    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

imageInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        sendMessage(e.target.files[0]);
    }
});

userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});