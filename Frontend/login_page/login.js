async function loginUser() {
    const username = document.querySelector('input[type="text"]').value;
    const password = document.querySelector('input[type="password"]').value;

    const data = { username, password };

    try {
        const response = await fetch('http://127.0.0.1:8000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            localStorage.setItem("farmer_user_id", result.user_id);
            localStorage.setItem("farmer_username", result.username);

            showToast(result.message, 'success');
            setTimeout(() => {
                window.location.href = '../dashboard/dashboard.html';
            }, 1000);

        } else {
            showToast(result.detail, 'error');
        }

    } catch (err) {
        console.error("Error:", err);
        showToast("Could not connect to server.", 'error');
    }
}