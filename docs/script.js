

const DOC_CONFIG = {
    theme: 'dark',
    scrollOffset: 80,
};

function initTheme() {
    const theme = localStorage.getItem('endfield-docs-theme') || 'dark';
    DOC_CONFIG.theme = theme;
    document.documentElement.dataset.theme = theme;
}

function toggleTheme() {
    DOC_CONFIG.theme = DOC_CONFIG.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = DOC_CONFIG.theme;
    localStorage.setItem('endfield-docs-theme', DOC_CONFIG.theme);
}


function initDrawer() {
    const drawerToggle = document.getElementById('drawer-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (!drawerToggle) return;
    
    drawerToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });
    
    // Close sidebar when clicking outside on small screens
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && 
            !sidebar.contains(e.target) && 
            !drawerToggle.contains(e.target) &&
            sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });
    
    // Close sidebar when navigating
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
            }
        });
    });
}



function generateTOC() {
    const toc = document.getElementById('toc');
    if (!toc) return;
    
    const tocList = toc.querySelector('ul');
    const content = document.querySelector('.content');
    
    // Collect all h2 and h3 headings
    const headings = content.querySelectorAll('h2, h3');
    
    headings.forEach(heading => {
        if (!heading.id) {
            heading.id = heading.textContent.toLowerCase().replace(/\s+/g, '-');
        }
        
        const level = parseInt(heading.tagName[1]);
        const li = document.createElement('li');
        const a = document.createElement('a');
        
        a.href = `#${heading.id}`;
        a.textContent = heading.textContent;
        a.className = 'toc-link';
        
        if (level === 3) {
            a.classList.add('toc-sub');
        }
        
        li.appendChild(a);
        tocList.appendChild(li);
    });
}

function initScrollspy() {
    const tocLinks = document.querySelectorAll('.toc-link');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                tocLinks.forEach(link => link.classList.remove('active'));
                const activeLink = document.querySelector(`.toc-link[href="#${entry.target.id}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }, {
        rootMargin: `-${DOC_CONFIG.scrollOffset}px 0px -66%`
    });
    
    // Also update sidebar nav links
    const sidebar = document.querySelector('.sidebar');
    const sidebarLinks = sidebar.querySelectorAll('.nav-link');
    
    const sidebarObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                sidebarLinks.forEach(link => link.classList.remove('active'));
                const activeLink = document.querySelector(`.sidebar .nav-link[href="#${entry.target.id}"]`);
                if (activeLink) {
                    activeLink.classList.add('active');
                }
            }
        });
    }, {
        rootMargin: `-${DOC_CONFIG.scrollOffset}px 0px -66%`
    });
    
    // Observe all content sections
    const sections = document.querySelectorAll('[id^="init"], [id^="get_"], [id^="model_"], [id^="examples"], #methods, #models');
    sections.forEach(section => {
        observer.observe(section);
        sidebarObserver.observe(section);
    });
}


function initSearch() {
    const searchTrigger = document.getElementById('search-trigger');
    if (!searchTrigger) return;
    
    searchTrigger.addEventListener('click', openSearchPalette);
    
    // Keyboard shortcut (Cmd+K or Ctrl+K)
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            openSearchPalette();
        }
    });
}

function openSearchPalette() {
    // Simple search: scroll to search section or navigate
    const query = prompt('Search methods or models (e.g., "get_showcase"):');
    if (!query) return;
    
    const lowerQuery = query.toLowerCase();
    
    // Try to find a matching method or model
    const allSections = document.querySelectorAll('[id^="init"], [id^="get_"], [id^="perform_"], [id^="check_"], [id^="update_"], [id^="model_"]');
    
    for (const section of allSections) {
        if (section.textContent.toLowerCase().includes(lowerQuery) && section.id.includes(lowerQuery)) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
            highlightElement(section);
            return;
        }
    }
    
    alert(`No results found for "${query}"`);
}

function highlightElement(element) {
    element.style.transition = 'background-color 0.3s';
    element.style.backgroundColor = 'var(--accent-soft)';
    setTimeout(() => {
        element.style.backgroundColor = '';
    }, 2000);
}

function enhanceLinks() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                window.history.pushState(null, '', link.getAttribute('href'));
            }
        });
    });
}


function addCopyButtons() {
    const codeBlocks = document.querySelectorAll('.code pre code');
    
    codeBlocks.forEach(codeBlock => {
        const code = codeBlock.textContent;
        
        const codeWrapper = codeBlock.parentElement;
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn icon-btn';
        copyBtn.title = 'Copy code';
        copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>';
        
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(code);
                const original = copyBtn.innerHTML;
                copyBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                setTimeout(() => {
                    copyBtn.innerHTML = original;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
        
        codeWrapper.style.position = 'relative';
        codeWrapper.appendChild(copyBtn);
    });
}

// Style for copy button
function injectCopyButtonStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .code {
            position: relative;
        }
        .code .copy-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }
        .code:hover .copy-btn {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
}


document.addEventListener('DOMContentLoaded', () => {
    // Theme
    initTheme();
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Drawer
    initDrawer();
    
    // Search
    initSearch();
    
    // Navigation
    enhanceLinks();
    
    // TOC & Scrollspy
    generateTOC();
    initScrollspy();
    
    // Code blocks
    injectCopyButtonStyles();
    addCopyButtons();
    
    // Syntax highlighting
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
    
    // Smooth scroll for all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && !this.classList.contains('nav-link')) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    window.history.pushState(null, '', href);
                }
            }
        });
    });
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    // Resume scrollspy when tab becomes visible
    if (!document.hidden) {
        initScrollspy();
    }
});
