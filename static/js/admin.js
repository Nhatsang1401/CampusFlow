
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("adminSidebar");
    const toggle = document.getElementById("sidebarToggle");

    if (sidebar && toggle) {
        toggle.addEventListener("click", () => {
            sidebar.classList.toggle("is-open");
        });

        document.addEventListener("click", (event) => {
            const clickedInsideSidebar = sidebar.contains(event.target);
            const clickedToggle = toggle.contains(event.target);

            if (
                window.innerWidth <= 760 &&
                !clickedInsideSidebar &&
                !clickedToggle
            ) {
                sidebar.classList.remove("is-open");
            }
        });
    }

    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm;

            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
