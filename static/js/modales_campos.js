function abrirModal(idModal) {
    const modal = document.getElementById(idModal);
    if (modal) {
        modal.classList.add("active");
    }
}

function inicializarModales(contenedor) {
    if (!contenedor) return;

    contenedor.querySelectorAll(".btn-cancelar").forEach(btn => {
        btn.addEventListener("click", () => {
            const idModal = btn.getAttribute("data-modal");
            const modal = document.getElementById(idModal);
            if (modal) modal.classList.remove("active");
        });
    });
}

