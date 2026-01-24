document.addEventListener("DOMContentLoaded", () => {
    const checkboxes = document.querySelectorAll('input[name="elemento"]');
    const campoOculto = document.getElementById("elemento_oculto");
    const formAccion = document.getElementById("formularioIngreso");
    const btnEliminar = document.getElementById("eliminar");
    const btnActualizar = document.getElementById("btn-actualizar");

    let seleccionados = [];

    // Actualizar IDs seleccionados
    checkboxes.forEach(chk => {
        chk.addEventListener("change", () => {
            seleccionados = Array.from(checkboxes)
                .filter(c => c.checked)
                .map(c => c.value);
            campoOculto.value = seleccionados.join(",");
            console.log("Seleccionados:", seleccionados);
        });
    });

    // Eliminar
    if (btnEliminar && formAccion) {
        btnEliminar.addEventListener("click", e => {
            e.preventDefault();
            if (seleccionados.length === 0) {
                alert("Selecciona al menos un usuario para eliminar.");
                return;
            }
            if (confirm("¿Eliminar usuario(s)?")) {
                const accionInput = document.createElement("input");
                accionInput.type = "hidden";
                accionInput.name = "accion";
                accionInput.value = "borrar";
                formAccion.appendChild(accionInput);
                formAccion.submit();
            }
        });
    }

    // Actualizar
    if (btnActualizar) {
        btnActualizar.addEventListener("click", e => {
            e.preventDefault();

            if (seleccionados.length !== 1) {
                alert("Selecciona exactamente un registro para actualizar.");
                return;
            }

            const idSeleccionado = seleccionados[0];
            console.log("ID seleccionado:", idSeleccionado);

            // URL base viene desde el atributo data-url del botón
            let baseUrl = btnActualizar.dataset.urlBase;
            baseUrl = baseUrl.replace(/\/$/, "").replace(/\/0$/, "");

            fetch(`${baseUrl}/${idSeleccionado}/`)
                .then(res => res.text())
                .then(html => {

                    // Reemplazar el contenido del modal
                    document.querySelector("#modal-container").innerHTML = html;

                    inicializarModalActualizar(document.querySelector("#modal-container"));
                    // Abrir modal normalmente
                    abrirModal("modal-actualizar");

                    
                })
                .catch(err => console.error("Error cargando modal:", err));
        });
    }
});
