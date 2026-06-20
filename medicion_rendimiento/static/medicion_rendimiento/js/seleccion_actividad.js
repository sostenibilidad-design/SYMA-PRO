document.addEventListener("DOMContentLoaded", function() {
    // 1. Lógica del Buscador de Actividades
    const buscadorActividad = document.getElementById("busqueda-actividad");
    if (buscadorActividad) {
        buscadorActividad.addEventListener("keyup", function() {
            let filtro = this.value.toLowerCase();
            let items = document.querySelectorAll(".actividad-item");

            items.forEach(function(item) {
                let texto = item.textContent.toLowerCase();
                item.style.display = texto.includes(filtro) ? "" : "none";
            });
        });
    }

    // 2. Lógica de Única Selección (Cambiar título y cerrar)
    const contenedorActividades = document.querySelector(".lista-actividades");
    const textoSeleccionado = document.getElementById("texto-actividad-seleccionada");
    const dropdownActividad = document.getElementById("dropdown-actividad");

    if (contenedorActividades) {
        // Usamos "delegación de eventos" para que sobreviva a la Actualización Ninja
        contenedorActividades.addEventListener("change", function(e) {
            if (e.target && e.target.classList.contains("radio-actividad")) {
                // Cambiar el texto del encabezado por la actividad seleccionada
                textoSeleccionado.textContent = e.target.value;
                // Ocultar el desplegable simulando un <select> normal
                dropdownActividad.style.display = "none";
            }
        });
    }
});