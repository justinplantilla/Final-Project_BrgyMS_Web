// Redirect to home page after splash screen
window.addEventListener('load', () => {
    // Wait 3 seconds then redirect to home
    setTimeout(() => {
        window.location.href = '/home';
    }, 3000);
});

// Optional: Click anywhere to skip splash screen
document.addEventListener('click', () => {
    window.location.href = '/home';
});