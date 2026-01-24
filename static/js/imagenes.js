document.addEventListener("DOMContentLoaded", function() {
    const modal = document.getElementById("modal-imagen");
    const modalImg = document.getElementById("imagen-grande");
    const cerrar = modal.querySelector(".cerrar-imagen");

    // Selecciona todas las imágenes de la tabla
    document.querySelectorAll(".celda-imagen img").forEach(img => {
        img.addEventListener("dblclick", function() {
            modal.style.display = "block";
            modalImg.src = this.src; // carga la imagen seleccionada
        });
    });

    // Cerrar al hacer clic en X
    cerrar.addEventListener("click", () => modal.style.display = "none");

});
