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

async function updateLocation() {
    const userId = localStorage.getItem("farmer_user_id");
    const newLoc = document.getElementById("newLocation").value.trim();
    if (!newLoc) return showToast("Please enter a valid location.", "error");

    try {
        const res = await fetch(`http://127.0.0.1:8000/users/${userId}/location`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ location: newLoc })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Location updated! Dashboard will reflect new weather.", "success");
            document.getElementById("newLocation").value = "";
        } else {
            showToast(data.detail || "Failed to update location", "error");
        }
    } catch (err) {
        showToast("Server connection error.", "error");
    }
}

async function updatePassword() {
    const userId = localStorage.getItem("farmer_user_id");
    const oldPass = document.getElementById("currentPassword").value;
    const newPass = document.getElementById("newPassword").value;
    
    if (!oldPass || !newPass) return showToast("Please fill both password fields.", "error");

    try {
        const res = await fetch(`http://127.0.0.1:8000/users/${userId}/password`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPass, new_password: newPass })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("Password updated successfully.", "success");
            document.getElementById("currentPassword").value = "";
            document.getElementById("newPassword").value = "";
        } else {
            showToast(data.detail || "Failed to update password", "error");
        }
    } catch (err) {
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