/**
 * Language Switching Module
 * Handles multi-language support and RTL/LTR switching
 */

class LanguageSwitcher {
    constructor(options = {}) {
        this.containerSelector = options.containerSelector || '[data-language-switcher]';
        this.apiEndpoint = options.apiEndpoint || '/accounts/api/language/';
        this.onLanguageChange = options.onLanguageChange || (() => {});
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateUIState();
    }

    setupEventListeners() {
        // Find all language switcher elements
        document.querySelectorAll(this.containerSelector).forEach(container => {
            // Language buttons
            const buttons = container.querySelectorAll('[data-language-code]');
            buttons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const langCode = btn.getAttribute('data-language-code');
                    this.setLanguage(langCode);
                });
            });

            // Language dropdown select
            const select = container.querySelector('select[name="language"]');
            if (select) {
                select.addEventListener('change', (e) => {
                    this.setLanguage(e.target.value);
                });
            }
        });
    }

    async setLanguage(languageCode) {
        try {
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    language: languageCode,
                }),
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                console.error('Language switch failed:', data.error);
                return;
            }

            // Update document language
            document.documentElement.lang = languageCode;

            // Update text direction if RTL
            const isRTL = data.language.is_rtl;
            this.setDirection(isRTL ? 'rtl' : 'ltr');

            // Store in localStorage
            localStorage.setItem('preferred_language', languageCode);

            // Trigger callback
            this.onLanguageChange({
                language: languageCode,
                isRTL: isRTL,
            });

            // Reload page after a short delay
            setTimeout(() => {
                location.reload();
            }, 100);

        } catch (error) {
            console.error('Language switch error:', error);
            alert('Failed to change language. Please try again.');
        }
    }

    setDirection(direction) {
        const html = document.documentElement;
        
        if (direction === 'rtl') {
            html.setAttribute('dir', 'rtl');
            html.classList.add('rtl');
            html.classList.remove('ltr');
        } else {
            html.setAttribute('dir', 'ltr');
            html.classList.add('ltr');
            html.classList.remove('rtl');
        }

        // Update body direction
        document.body.setAttribute('dir', direction);
    }

    updateUIState() {
        const currentLang = document.documentElement.lang || 'en';
        
        // Update active state on buttons
        document.querySelectorAll('[data-language-code]').forEach(btn => {
            const btnLang = btn.getAttribute('data-language-code');
            if (btnLang === currentLang) {
                btn.classList.add('active');
                btn.setAttribute('aria-pressed', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');
            }
        });

        // Update dropdown select
        const select = document.querySelector('select[name="language"]');
        if (select) {
            select.value = currentLang;
        }
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }

    /**
     * Get list of available languages
     */
    async getAvailableLanguages() {
        try {
            const response = await fetch(this.apiEndpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data.available || [];

        } catch (error) {
            console.error('Failed to get languages:', error);
            return [];
        }
    }

    /**
     * Get current language info
     */
    async getCurrentLanguage() {
        try {
            const response = await fetch(this.apiEndpoint, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            return data.current || {};

        } catch (error) {
            console.error('Failed to get current language:', error);
            return {};
        }
    }
}

// Initialize on DOM ready if auto-init is enabled
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.querySelector('[data-language-switcher]')) {
            window.languageSwitcher = new LanguageSwitcher();
        }
    });
} else {
    if (document.querySelector('[data-language-switcher]')) {
        window.languageSwitcher = new LanguageSwitcher();
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.LanguageSwitcher = LanguageSwitcher;
}
