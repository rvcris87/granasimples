(function () {
    const storageKey = "granasimples-theme";
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

    function getInitialTheme() {
        const savedTheme = localStorage.getItem(storageKey);
        if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
        return prefersDark.matches ? "dark" : "light";
    }

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            const nextLabel = theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro";
            button.setAttribute("aria-label", nextLabel);
            button.setAttribute("title", nextLabel);
        });
    }

    applyTheme(getInitialTheme());

    window.GranaTheme = {
        get current() {
            return document.documentElement.dataset.theme || getInitialTheme();
        },
        toggle() {
            const nextTheme = this.current === "dark" ? "light" : "dark";
            localStorage.setItem(storageKey, nextTheme);
            applyTheme(nextTheme);
            window.dispatchEvent(new CustomEvent("grana-theme-change", { detail: { theme: nextTheme } }));
        }
    };

    document.addEventListener("DOMContentLoaded", () => {
        applyTheme(window.GranaTheme.current);
        document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
            button.addEventListener("click", () => window.GranaTheme.toggle());
        });

        const mobileToggle = document.querySelector("[data-mobile-nav-toggle]");
        const nav = document.querySelector("[data-mobile-nav]");
        if (mobileToggle && nav) {
            mobileToggle.addEventListener("click", () => {
                const isOpen = nav.classList.toggle("is-open");
                mobileToggle.setAttribute("aria-expanded", String(isOpen));
            });
        }
    });
})();
