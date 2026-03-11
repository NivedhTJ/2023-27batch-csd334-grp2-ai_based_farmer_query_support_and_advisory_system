// dashboard.js

const TIPS = [
    "Rotate your crops annually to prevent soil depletion and break pest cycles.",
    "Water your plants early in the morning to minimize evaporation and fungal diseases.",
    "Use cover crops like clover or rye during the off-season to improve soil health.",
    "Test your soil pH regularly. Most vegetables prefer a slightly acidic pH between 6.0 and 7.0.",
    "Mulch around your plants to retain moisture, suppress weeds, and regulate soil temperature.",
    "Encourage beneficial insects like ladybugs by planting companion flowers like marigolds.",
    "Over-fertilizing can be just as harmful as under-fertilizing. Always follow recommended rates.",
    "Keep records of your planting dates, yields, and weather conditions for future reference."
];

document.addEventListener("DOMContentLoaded", () => {
    const userId = localStorage.getItem("farmer_user_id");
    const username = localStorage.getItem("farmer_username");

    if (!userId || !username) return window.location.href = "../login_page/login.html";

    document.getElementById("welcome-message").textContent = `Welcome back, ${username.charAt(0).toUpperCase() + username.slice(1)}!`;
    document.getElementById("daily-tip").textContent = TIPS[Math.floor(Math.random() * TIPS.length)];

    loadWeather(userId);
});

async function loadWeather(userId) {
    const content = document.getElementById("weather-content");
    try {
        const response = await fetch(`http://127.0.0.1:8000/weather/${userId}`);
        const data = await response.json();

        if (response.ok && data.weather) {
            const { temperature, description, humidity, wind_speed } = data.weather;
            content.innerHTML = `
                <div class="weather-main">
                    <span class="weather-temp">${Math.round(temperature)}°C</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem;">${data.location}</div>
                        <div class="weather-desc">${description}</div>
                    </div>
                </div>
                <div class="weather-details">
                    <div class="weather-item">💧 Humidity: ${humidity}%</div>
                    <div class="weather-item">💨 Wind: ${wind_speed} m/s</div>
                </div>`;
        } else throw new Error(data.message || 'Unknown error');
    } catch (err) {
        content.innerHTML = `<p style="color: #d32f2f;">Failed to load weather data.</p>`;
    }
}

function comingSoon(e) {
    e.preventDefault();
    (typeof showToast === 'function' ? showToast : alert)("Crop Recommendation is coming soon!", "info");
}

function logout() {
    ['farmer_user_id', 'farmer_username'].forEach(k => localStorage.removeItem(k));
    window.location.href = "../login_page/login.html";
}
