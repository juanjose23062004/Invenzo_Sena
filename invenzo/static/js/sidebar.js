// sidebar.js — reemplaza el archivo actual con este contenido

// 1) Aseguramos que lucide haya renderizado los iconos.
//    Si ya se llamó desde el HTML, esto es idempotente.
if (typeof lucide !== "undefined" && typeof lucide.createIcons === "function") {
    lucide.createIcons();
}

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.querySelector(".sidebar");
    const closeWrapper = document.querySelector(".close-sidebar"); // el contenedor
    // Aseguramos que el sidebar arranque abierto por defecto (en escritorio).
    if (sidebar && !sidebar.classList.contains("active")) {
        sidebar.classList.add("active");
    }

    // Función para hacer toggle del sidebar
    const toggleSidebar = () => {
        if (!sidebar) return;
        sidebar.classList.toggle("active");
    };

    // Delegación de eventos: escuchamos clicks en el documento
    // y verificamos si el click fue en o dentro del icono skip-forward (o su svg generado)
    document.addEventListener("click", (e) => {
        // Si el click está dentro del sidebar no hacemos nada aquí (salvo para el close)
        if (sidebar && sidebar.contains(e.target)) return;

        // Matchers que detectan el icono skip-forward en sus posibles formas:
        // - el elemento original: <i data-lucide="skip-forward" class="menu-toggle">
        // - el svg generado por lucide (puede tener clase lucide-skip-forward o data-lucide)
        const clickedToggle =
            e.target.closest('.menu-toggle') ||
            e.target.closest('[data-lucide="skip-forward"]') ||
            e.target.closest('.lucide-skip-forward') ||
            e.target.closest('svg[data-lucide="skip-forward"]');

        if (clickedToggle) {
            // Si se hizo click en el icono, togglear el sidebar
            toggleSidebar();
            return;
        }

        // Si estamos en móvil (ancho <= 850) y se hizo click fuera del sidebar, lo cerramos
        if (window.innerWidth <= 850 && sidebar && !sidebar.contains(e.target)) {
            sidebar.classList.remove("active");
        }
    });

    // Cerrar con el botón X (close-sidebar existirá en el sidebar)
    if (closeWrapper) {
        closeWrapper.addEventListener("click", (e) => {
            // si el ícono X es un <i> hijo o el propio contenedor, cerramos
            if (sidebar) sidebar.classList.remove("active");
            e.stopPropagation();
        });
    }

    // Por seguridad: también permitir tecla ESC para cerrar en móvil
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && window.innerWidth <= 850 && sidebar) {
            sidebar.classList.remove("active");
        }
    });
});
