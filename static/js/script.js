// Redirect to login page
function goToLogin() {
    window.location.href = '/login';
}

// Smooth scroll to learn more section
function scrollToLearnMore() {
    // Kung may learn more section, scroll doon
    const learnMoreSection = document.getElementById('learn-more');
    if (learnMoreSection) {
        learnMoreSection.scrollIntoView({ behavior: 'smooth' });
    } else {
        // Temporary alert kung wala pang section
        alert('Learn More section coming soon!');
    }
}

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    
    if (currentScroll <= 0) {
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.2)';
    }
    
    lastScroll = currentScroll;
});

// Add floating animation to buttons
const buttons = document.querySelectorAll('.btn');
buttons.forEach(button => {
    button.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px)';
    });
    
    button.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0)';
    });
});