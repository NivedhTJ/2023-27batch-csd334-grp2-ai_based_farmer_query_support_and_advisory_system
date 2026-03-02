window.onload = function () {
    const username = localStorage.getItem("farmer_username");
    const userId = localStorage.getItem("farmer_user_id");

    if (!username || !userId) {
        if (window.showToast) showToast("You are not logged in.", "error");
        setTimeout(() => {
            window.location.href = "../login_page/login.html";
        }, 1000);
        return;
    }

    document.getElementById("username").innerText = username;
    document.getElementById("userId").innerText = userId;
};

function goToFeedback() {
    window.location.href = "../feedback_form/feedback_form.html";
}

async function clearHistory() {
    const userId = localStorage.getItem("farmer_user_id");

    if (!confirm("Are you sure? This will permanently delete your chat history.")) return;

    try {
        const response = await fetch(`http://127.0.0.1:8000/clear/${userId}`, {
            method: "DELETE"
        });

        if (response.ok) {
            showToast("Chat history cleared successfully.", "success");
        } else {
            showToast("Failed to clear history.", "error");
        }

    } catch (err) {
        console.error(err);
        showToast("Server connection error.", "error");
    }
}

function logout() {
    localStorage.removeItem("farmer_user_id");
    localStorage.removeItem("farmer_username");
    localStorage.removeItem("current_session_id");

    showToast("Logged out successfully.", "success");
    setTimeout(() => {
        window.location.href = "../login_page/login.html";
    }, 1000);
}