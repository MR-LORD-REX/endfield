document.addEventListener('DOMContentLoaded', () => {
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.getElementById('sidebar');
    const searchInput = document.getElementById('searchInput');
    const navItems = document.querySelectorAll('.nav-item');
    const cards = document.querySelectorAll('.card');

    // Toggle sidebar on mobile
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            !sidebar.contains(e.target) && 
            !mobileToggle.contains(e.target) &&
            sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });

    // Search functionality
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();

            // Filter nav items
            navItems.forEach(item => {
                const text = item.textContent.toLowerCase();
                if (text.includes(term)) {
                    item.parentElement.style.display = 'block';
                } else {
                    item.parentElement.style.display = 'none';
                }
            });

            // Filter content cards
            cards.forEach(card => {
                const title = card.querySelector('h3').textContent.toLowerCase();
                if (title.includes(term)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Active state on scroll
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -80% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Remove active class from all
                navItems.forEach(item => item.classList.remove('active'));
                
                // Add active class to current
                const id = entry.target.getAttribute('id');
                const activeNav = document.querySelector(`.nav-item[href="#${id}"]`);
                if (activeNav) {
                    activeNav.classList.add('active');
                    // Scroll sidebar to active item if needed
                    activeNav.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        });
    }, observerOptions);

    cards.forEach(card => {
        observer.observe(card);
    });
    
    // Smooth scrolling for sidebar links
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const targetId = item.getAttribute('href');
            // Allow default behavior but close sidebar on mobile
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
    });
});
