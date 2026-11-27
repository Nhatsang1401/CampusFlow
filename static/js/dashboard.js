"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector("#appSidebar");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const backdrop = document.querySelector(".sidebar-backdrop");
    const closeElements = document.querySelectorAll("[data-sidebar-close]");

    const openSidebar = () => {
        if (!sidebar || !toggle || !backdrop) return;

        sidebar.classList.add("is-open");
        backdrop.classList.add("is-visible");
        toggle.setAttribute("aria-expanded", "true");
        document.body.style.overflow = "hidden";
    };

    const closeSidebar = () => {
        if (!sidebar || !toggle || !backdrop) return;

        sidebar.classList.remove("is-open");
        backdrop.classList.remove("is-visible");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
    };

    toggle?.addEventListener("click", () => {
        const isOpen = sidebar?.classList.contains("is-open");

        if (isOpen) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    closeElements.forEach((element) => {
        element.addEventListener("click", closeSidebar);
    });

    sidebar?.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            if (window.innerWidth <= 760) {
                closeSidebar();
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeSidebar();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 760) {
            closeSidebar();
        }
    });

    // Ngày hiện tại theo múi giờ Việt Nam.
    const dateElement = document.querySelector("[data-current-date]");

    if (dateElement) {
        const now = new Date();

        dateElement.textContent = new Intl.DateTimeFormat("vi-VN", {
            timeZone: "Asia/Ho_Chi_Minh",
            weekday: "long",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        }).format(now);
    }

    // Đánh dấu menu đang được chọn.
    const currentPath = window.location.pathname;

    sidebar?.querySelectorAll(".sidebar-link[href]").forEach((link) => {
        const href = link.getAttribute("href");

        if (!href || href.startsWith("#")) return;

        try {
            const linkUrl = new URL(href, window.location.origin);

            if (linkUrl.pathname === currentPath) {
                sidebar.querySelectorAll(".sidebar-link").forEach((item) => {
                    item.classList.remove("active");
                    item.querySelector(".nav-active-indicator")?.remove();
                });

                link.classList.add("active");
            }
        } catch {
            // Bỏ qua liên kết không hợp lệ.
        }
    });
});