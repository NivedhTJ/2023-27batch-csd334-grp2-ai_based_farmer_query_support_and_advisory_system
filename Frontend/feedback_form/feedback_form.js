document.getElementById("feedbackForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const mobile = document.getElementById("mobile").value.trim();
    const category = document.getElementById("category").value;
    const rating = document.querySelector('input[name="rating"]:checked')?.value;
    const feedback = document.getElementById("feedback").value.trim();

    if (!name || !mobile || !category || !rating || !feedback) {
        showToast("Please fill all fields.", 'warning');
        return;
    }

    const payload = {
        name: name,
        mobile: mobile,
        category: category,
        rating: parseInt(rating),
        feedback: feedback
    };

    try {
        const response = await fetch("http://127.0.0.1:8000/submit-feedback", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showToast("Thank you! Your feedback has been submitted.", 'success');
            document.getElementById("feedbackForm").reset();
        } else {
            showToast("Error: " + result.detail, 'error');
        }

    } catch (error) {
        console.error("Submission error:", error);
        showToast("Could not connect to server.", 'error');
    }
});
