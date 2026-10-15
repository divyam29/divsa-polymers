// Forms use native POST/redirect navigation so flash messages render once.
document.addEventListener('DOMContentLoaded', function () {
    // --- Scroll Animation Handler (Intersection Observer) ---
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: '0px 0px -50px 0px' });

        animatedElements.forEach(el => observer.observe(el));
    } else {
        // Fallback for older browsers
        animatedElements.forEach(el => el.classList.add('is-visible'));
    }

    // --- Mobile Menu Toggle ---
    const menuToggle = document.getElementById('menu-toggle');
    const navLinks = document.querySelectorAll('.nav-links a');
    if (navLinks) {
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (menuToggle) menuToggle.checked = false; // Close menu when a link is clicked
            });
        });
    }
});
