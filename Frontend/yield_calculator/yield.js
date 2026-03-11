// yield.js

// Average yield estimates per acre (in tons) - Median values used for estimation
const CROP_YIELDS = {
    wheat: 1.75,       // 1.5 - 2
    rice: 2.75,        // 2.5 - 3
    corn: 3.5,         // 3 - 4
    soybean: 1.25,     // 1 - 1.5
    potato: 12.5,      // 10 - 15
    cotton: 0.75,      // 0.5 - 1
    sugarcane: 35      // 30 - 40
};

window.onload = function() {
    const userId = localStorage.getItem("farmer_user_id");
    if (!userId) {
        if(window.showToast) showToast("Not logged in.", "error");
        setTimeout(() => window.location.href = "../login_page/login.html", 1000);
    }
};

function calculateYield(event) {
    event.preventDefault();
    
    const cropType = document.getElementById("cropType").value;
    const areaSize = parseFloat(document.getElementById("areaSize").value);
    const priceKg = parseFloat(document.getElementById("priceKg").value);

    if(!cropType || isNaN(areaSize) || isNaN(priceKg)) {
        if(window.showToast) showToast("Please fill all fields correctly", "error");
        return;
    }

    // 1 Ton = 1000 kg
    const tonsPerAcre = CROP_YIELDS[cropType];
    const totalTons = tonsPerAcre * areaSize;
    const totalKg = totalTons * 1000;
    const totalRevenue = totalKg * priceKg;

    // Format numbers
    const formatNumber = (num, decimals) => num.toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    
    // Display results
    document.getElementById("resYield").textContent = formatNumber(totalTons, 2) + " t";
    document.getElementById("resKg").textContent = formatNumber(totalKg, 0) + " kg";
    document.getElementById("resRevenue").textContent = "₹" + formatNumber(totalRevenue, 2);

    // Show card smoothly
    const resCard = document.getElementById("resultCard");
    resCard.style.display = "flex";
    
    if(window.showToast) showToast("Calculated successfully!", "success");
}
