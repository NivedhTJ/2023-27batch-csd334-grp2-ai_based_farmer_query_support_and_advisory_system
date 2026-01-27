const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");

function appendMessage(sender, text, isLoader = false) {
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

    if (isLoader) {
        bubble.classList.add("thinking");
        bubble.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        messageDiv.id = "ai-thinking"; // Unique ID to find and remove it later
    } else {
        bubble.textContent = text;
    }

    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; 
}

async function sendMessage() {
    const question = userInput.value.trim();
    const userId = localStorage.getItem("farmer_user_id") || 1; 

    if (!question) return;

    appendMessage("user", question);
    userInput.value = "";
    
    appendMessage("ai", "", true);

    try {
        const response = await fetch("http://127.0.0.1:8000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                user_id: parseInt(userId), 
                query: question 
            })
        });

        const loader = document.getElementById("ai-thinking");
        if (loader) loader.remove();

        if (!response.ok) throw new Error("Server error");

        const data = await response.json();
        
        appendMessage("ai", data.response);

    } catch (error) {
        console.error("Error:", error);
        const loader = document.getElementById("ai-thinking");
        if (loader) loader.remove();
        appendMessage("ai", "Sorry, I couldn't connect. Try again.");
    }
}

userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});