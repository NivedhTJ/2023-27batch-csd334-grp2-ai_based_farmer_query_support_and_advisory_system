// toast.js
window.showToast = function(message, type = 'info') {
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    // Icons based on type (Requires FontAwesome)
    let icon = '';
    if (type === 'success') {
        icon = '<i class="fa-solid fa-circle-check"></i>';
    } else if (type === 'error') {
        icon = '<i class="fa-solid fa-circle-exclamation"></i>';
    } else if (type === 'warning') {
        icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    } else {
        icon = '<i class="fa-solid fa-circle-info"></i>';
    }
    
    toast.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-message">${message}</span>`;
    
    toastContainer.appendChild(toast);
    
    // Request reflow to enable transition
    void toast.offsetWidth;

    // Trigger animation
    toast.classList.add('show');
    
    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => {
            toast.remove();
            if (toastContainer.children.length === 0) {
                toastContainer.remove();
            }
        });
    }, 3000);
}
