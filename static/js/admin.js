"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("adminSidebar");
    const toggle = document.getElementById("sidebarToggle");

    const closeSidebar = () => {
        if (!sidebar || !toggle) return;
        sidebar.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
    };

    if (sidebar && toggle) {
        toggle.addEventListener("click", () => {
            const isOpen = sidebar.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });

        document.addEventListener("click", (event) => {
            const isMobile = window.matchMedia("(max-width: 850px)").matches;
            if (isMobile && sidebar.classList.contains("is-open") &&
                !sidebar.contains(event.target) && !toggle.contains(event.target)) {
                closeSidebar();
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") closeSidebar();
        });

        window.addEventListener("resize", () => {
            if (!window.matchMedia("(max-width: 850px)").matches) closeSidebar();
        });
    }

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm;
            if (message && !window.confirm(message)) event.preventDefault();
        });
    });
});
