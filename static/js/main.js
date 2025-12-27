// --- Simple Form Submission Handler (for demo) ---
document.addEventListener('DOMContentLoaded', function () {
    const distributorForm = document.getElementById('distributor-form');
    if (distributorForm) {
        distributorForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(distributorForm);

            // Send the form to the Flask endpoint
            fetch('/submit-inquiry', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                // If server redirected, follow it in the browser so flashed messages render
                if (response.redirected) {
                    window.location = response.url;
                } else {
                    // Fallback: go to dealership section
                    window.location = '/#dealership';
                }
            })
            .catch(err => {
                console.error('Form submit error:', err);
                alert('There was an error submitting the form. Please try again later.');
            });
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
