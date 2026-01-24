function inicializarDespliegue(contenedor) {

    const bloques = contenedor.querySelectorAll(".funcionalidades-box");

    bloques.forEach((bloque) => {
        const areaToggle = bloque.querySelector(".titulo-funcionalidades");
        const areaDropdown = bloque.querySelector(".contenido-funcionalidades.dropdown");
        const checkboxes = bloque.querySelectorAll(".area-checkbox");
        const titleText = areaToggle?.querySelector("strong");
        const buscador = bloque.querySelector('input[type="text"][placeholder="Buscar empleado..."]');
        const items = bloque.querySelectorAll(".area-item");

        if (!areaToggle || !areaDropdown || !titleText) return;

        // Toggle
        areaToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            areaDropdown.style.display =
                areaDropdown.style.display === "block" ? "none" : "block";
        });

        // Cerrar al hacer click fuera
        document.addEventListener("click", (e) => {
            if (!e.target.closest(".funcionalidades-box")) {
                areaDropdown.style.display = "none";
            }
        });

        // Contador
        if (!titleText.dataset.original) {
            titleText.dataset.original = titleText.textContent.trim();
        }

        checkboxes.forEach(cb => {
            cb.addEventListener("change", () => {
                const seleccionados = bloque.querySelectorAll(".area-checkbox:checked").length;
                titleText.textContent = titleText.dataset.original +
                    (seleccionados > 0 ? ` (${seleccionados} seleccionados)` : "");
            });
        });

        // Buscador
        if (buscador) {
            buscador.addEventListener("keyup", () => {
                const texto = buscador.value.toLowerCase().trim();
                items.forEach(item => {
                    item.style.display = item.innerText.toLowerCase().includes(texto)
                        ? "block"
                        : "none";
                });
            });
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Para foto_inicio
    const inputInicio = document.getElementById("id_foto_inicio");
    const textInicio = document.getElementById("fileText_inicio");  // ID único

    if (inputInicio && textInicio) {
        inputInicio.addEventListener("change", () => {
            textInicio.textContent = inputInicio.files.length > 0 ? "Archivo adjunto" : "Insertar imagen";
        });
    }

    // Para foto_fin
    const inputFin = document.getElementById("id_foto_fin");
    const textFin = document.getElementById("fileText_fin");  // ID único

    if (inputFin && textFin) {
        inputFin.addEventListener("change", () => {
            textFin.textContent = inputFin.files.length > 0 ? "Archivo adjunto" : "Insertar imagen";
        });
    }
});
