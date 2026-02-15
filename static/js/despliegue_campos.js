function inicializarDespliegue(contenedor) {
    // Buscamos todos los contenedores de selección
    const bloques = contenedor.querySelectorAll(".funcionalidades-box");

    bloques.forEach((bloque) => {
        const areaToggle = bloque.querySelector(".titulo-funcionalidades");
        const areaDropdown = bloque.querySelector(".contenido-funcionalidades.dropdown");
        const checkboxes = bloque.querySelectorAll(".area-checkbox");
        const titleText = areaToggle?.querySelector("strong");
        
        // CORRECCIÓN: Buscamos por CLASE en lugar de por el texto del placeholder
        const buscador = bloque.querySelector(".input-busqueda-empleado");
        const items = bloque.querySelectorAll(".area-item");

        if (!areaToggle || !areaDropdown || !titleText) return;

        // Abrir / Cerrar dropdown
        areaToggle.addEventListener("click", (e) => {
            e.stopPropagation();
            const estaAbierto = areaDropdown.style.display === "block";
            areaDropdown.style.display = estaAbierto ? "none" : "block";
        });

        // Contador de seleccionados
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

        // BUSCADOR CORREGIDO
        if (buscador) {
            buscador.addEventListener("input", () => { // Usamos 'input' en vez de 'keyup' para mayor fluidez
                const texto = buscador.value.toLowerCase().trim();
                items.forEach(item => {
                    // Buscamos el texto dentro del label o el strong
                    const nombre = item.textContent.toLowerCase();
                    item.style.display = nombre.includes(texto) ? "block" : "none";
                });
            });
        }
    });
}

// Asegúrate de llamar a la función para los modales
document.addEventListener("DOMContentLoaded", () => {
    // Inicializar para el cuerpo del documento (esto cubrirá los bloques visibles)
    inicializarDespliegue(document.body);
    
    // Si tus modales se cargan dinámicamente o necesitas re-inicializar:
    const modalActividad = document.getElementById("modal-actividad");
    const modalAlertas = document.getElementById("modal-config-alertas");
    
    if(modalActividad) inicializarDespliegue(modalActividad);
    if(modalAlertas) inicializarDespliegue(modalAlertas);
});