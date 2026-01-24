document.addEventListener("DOMContentLoaded", () => {
    console.log("⚙️ Sistema de modales dinámicos cargado");

    const modalContainer = document.getElementById("modal-container");

    if (!modalContainer) {
        console.warn("No existe #modal-container en el DOM.");
        return;
    }

    // ============================
    // 1️⃣ ABRIR MODAL DINÁMICO
    // ============================
    document.addEventListener("click", async (e) => {

        // Solo botones que tengan esta clase
        const btn = e.target.closest(".btn-open-modal");
        if (!btn) return;

        e.preventDefault();

        const url = btn.dataset.url;           // URL de carga
        const modalId = btn.dataset.modal;     // ID que tendrá el modal
        const initFunction = btn.dataset.init; // nombre del inicializador JS

        if (!url) {
            console.error("El botón no tiene data-url");
            return;
        }

        console.log("🔄 Cargando modal desde:", url);

        // Loading temporal
        modalContainer.innerHTML = `
            <div class="loading">Cargando...</div>
        `;

        try {
            const resp = await fetch(url);
            if (!resp.ok) throw new Error("Error al cargar modal");
            const html = await resp.text();

            modalContainer.innerHTML = html;

            // Abrir modal
            abrirModal(modalId);

            // Ejecutar función inicializadora si existe
            if (initFunction && typeof window[initFunction] === "function") {
                console.log("➡️ Ejecutando inicializador:", initFunction);
                window[initFunction]();
            }

        } catch (err) {
            console.error("❌ Error al cargar modal:", err);
            alert("No se pudo cargar el modal.");
        }
    });

    // ============================
    // 2️⃣ CERRAR MODAL DESDE BOTONES
    // ============================
    document.addEventListener("click", (e) => {
        const btnClose = e.target.closest(".btn-cancelar");
        if (!btnClose) return;

        e.preventDefault();
        const modalId = btnClose.dataset.modal;
        cerrarModal(modalId);
    });

    // ============================
    // 3️⃣ FUNCIONES GLOBALES
    // ============================
    window.abrirModal = function(idModal) {
        const modal = document.getElementById(idModal);
        if (modal) modal.style.display = "block";
    };

    window.cerrarModal = function(idModal) {
        const modal = document.getElementById(idModal);
        if (!modal) return;

        modal.style.display = "none";

        const form = modal.querySelector("form");
        if (form) form.reset();
    };
});
