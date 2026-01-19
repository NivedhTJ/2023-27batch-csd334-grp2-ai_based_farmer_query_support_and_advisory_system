const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");

function appendMessage(sender, text) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);


    if (sender === "ai") {
        const avatar = document.createElement("img");
        avatar.src = "avatar.png";
        avatar.classList.add("avatar");
        messageDiv.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.textContent = text;

    messageDiv.appendChild(bubble);

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; 
}

async function sendMessage() {
    const question = userInput.value.trim();
    if (!question) return;

    appendMessage("user", question);
    userInput.value = "";

    try {
        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: question })
        });

        if (!response.ok) throw new Error("Server error");

        const data = await response.json();
        appendMessage("ai", data.response);

    } catch (error) {
        console.error("Error:", error);
        appendMessage("ai", "Sorry, I couldn't get a response. Please try again.");
    }
}

userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") sendMessage();
});