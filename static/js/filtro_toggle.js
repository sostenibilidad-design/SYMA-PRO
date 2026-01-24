document.addEventListener("DOMContentLoaded", () => {
    const filtroPanel = document.getElementById("filtro-panel");
    const btnAbrirFiltro = document.getElementById("btn-filtro"); // este es el botón que abre el filtro
    const contenedor = document.querySelector(".contenedor_principal");
    const menuLateral = document.getElementById("menu-hamburguesa");

    if (!filtroPanel || !btnAbrirFiltro || !contenedor) return;

    btnAbrirFiltro.addEventListener("click", () => {
        // Cierra el menú lateral si está abierto
        if (menuLateral && menuLateral.classList.contains("active")) {
            menuLateral.classList.remove("active");
        }

        // Alterna el filtro
        filtroPanel.classList.toggle("active");
        contenedor.classList.toggle("filtro-activo");
    });

    // Opción: cerrar el filtro al hacer clic fuera
    document.addEventListener("click", (e) => {
        if (
            filtroPanel.classList.contains("active") &&
            !filtroPanel.contains(e.target) &&
            e.target !== btnAbrirFiltro
        ) {
            filtroPanel.classList.remove("active");
            contenedor.classList.remove("filtro-activo");
        }
    });
});
