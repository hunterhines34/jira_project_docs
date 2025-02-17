// Modal handling
document.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'modal') {
        document.getElementById('modal').classList.remove('hidden');
        document.body.classList.add('modal-open');
    }
});

// Close modal on background click
document.addEventListener('click', function(evt) {
    if (evt.target.id === 'modal') {
        evt.target.classList.add('hidden');
        document.body.classList.remove('modal-open');
    }
});

// Handle notifications
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } transition-opacity duration-300`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// HTMX extensions
htmx.defineExtension('notification', {
    onEvent: function(name, evt) {
        if (name === "htmx:afterRequest") {
            const status = evt.detail.xhr.status;
            const response = evt.detail.xhr.response;
            
            if (status === 200) {
                if (response.message) {
                    showNotification(response.message);
                }
            } else if (status >= 400) {
                showNotification(response.error || 'An error occurred', 'error');
            }
        }
    }
}); 