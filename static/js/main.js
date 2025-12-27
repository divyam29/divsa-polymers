// --- Simple Form Submission Handler (for demo) ---
document.addEventListener('DOMContentLoaded', function () {
    const distributorForm = document.getElementById('distributor-form');
    if (distributorForm) {
        distributorForm.addEventListener('submit', function (e) {
            e.preventDefault(); // Prevent actual submission

            // Get form data
            const formData = new FormData(distributorForm);
            const data = Object.fromEntries(formData.entries());

            // Log data to console (in a real site, you'd send this to a server)
            console.log('Form Submitted:', data);

            // Show a success message
            alert('Thank you for your inquiry! We will get back to you within 24 hours.');

            // Clear the form
            distributorForm.reset();
        });
    }

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
