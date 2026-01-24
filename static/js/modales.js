/*  modales.js  (único para todo el sitio)  */
document.addEventListener("DOMContentLoaded", () => {
  /* ---------- capturas globales ---------- */
    const formulario      = document.getElementById("formularioIngreso");
    const btnEnviar       = document.getElementById("btnEnviar");
    const btnEliminar     = document.getElementById("btnEliminar");
    const btnEditar       = document.getElementById("btnEditar");

    const exitoEl         = document.getElementById("exitoModal");
    const advertenciaEl   = document.getElementById("advertenciaModal");
    const confirmarEl     = document.getElementById("confirmarModal");
    const btnConfirmar    = document.getElementById("btnConfirmar");
    const modalElemento   = document.getElementById("modalUnElemento");
    const modalInexistente = document.getElementById("modaldatoInexistente")

    /* ---------- instancias (solo si existen) ---------- */
    const modalExito       = exitoEl       ? new bootstrap.Modal(exitoEl)         : null;
    const modalAdvertencia = advertenciaEl ? new bootstrap.Modal(advertenciaEl)   : null;
    const modalConfirmar   = confirmarEl   ? new bootstrap.Modal(confirmarEl)     : null;
    const modalUnElemento  = modalElemento  ? new bootstrap.Modal(modalElemento)  : null;
    const modaldatoInexistente = modalInexistente ? new bootstrap.Modal(modalInexistente) : null;

    /* ---------- 1) mostrar modal de éxito proveniente del backend ---------- */
    if (typeof mostrarModal !== "undefined" && mostrarModal === "true" && modalExito) {
        modalExito.show();

        /* redirección opcional solo cuando lo definas en la plantilla */
        if (typeof redirLogin !== "undefined" && redirLogin === "true") {
            setTimeout(() => (window.location.href = "/login/"), 3000);
        }
    }

    
    /* ---------- 1.b) mostrar modal de lote/dato inexistente ---------- */
    if (typeof mostrarModalInexistente !== "undefined" && 
        mostrarModalInexistente === "true" && 
        modaldatoInexistente) {
        modaldatoInexistente.show();
    }

    /* ---------- 2) validación del envío ---------- */
    if (btnEnviar && formulario) {
        btnEnviar.addEventListener("click", () => {
            if (formulario.checkValidity()) {
                
                /* a) Hay modalConfirmar ⇒ ventana “¿Estás seguro?” */
                if (modalConfirmar) {
                    modalConfirmar.show();
                }
                /* b) No hay confirmación ⇒ enviamos directo                */
                else { 
                    formulario.submit();
                }
            } else {
                /* formulario incompleto ⇒ advertimos solo si existe modalAdvertencia */
                modalAdvertencia ? modalAdvertencia.show() : formulario.reportValidity();
            }
        });
    }

    if (btnEliminar && formulario) {
        btnEliminar.addEventListener("click", (e) => {
            e.preventDefault(); // evitar envío por defecto

            if (formulario.checkValidity()) {

                const seleccionados = Array.from(document.querySelectorAll('input[name="elemento"]'))
                                    .filter(c => c.checked)
                                    .map(c => c.value);

                if (seleccionados.length === 0) {
                    modalAdvertencia ? modalAdvertencia.show() : alert("");
                    return;
                }

                // actualizar global para otros usos si quieres
                window.ids = seleccionados;

                
                /* a) Hay modalConfirmar ⇒ ventana “¿Estás seguro?” */
                if (modalConfirmar) {
                    modalConfirmar.show();
                }
                /* b) No hay confirmación ⇒ enviamos directo                */
                else { 
                    formulario.submit();
                }
            } else {
                /* formulario incompleto ⇒ advertimos solo si existe modalAdvertencia */
                modalAdvertencia ? modalAdvertencia.show() : formulario.reportValidity();
            }
        });
    }

    if (btnEditar && formulario) {
        btnEditar.addEventListener("click", (e) => {
            e.preventDefault(); // evitar envío por defecto

            if (formulario.checkValidity()) {

                const seleccionados = Array.from(document.querySelectorAll('input[name="elemento"]'))
                                    .filter(c => c.checked)
                                    .map(c => c.value);

                if (seleccionados.length === 0) {
                    modalAdvertencia ? modalAdvertencia.show() : alert("");
                    return;
                }

                // actualizar global para otros usos si quieres
                window.ids = seleccionados;

                if (window.ids.length > 1) {
                    modalUnElemento ? modalUnElemento.show() : alert("");
                    return;
                }
                
                // actualizar global para otros usos si quieres
                window.ids = seleccionados;
                
                setTimeout(() => {
                    const accionInput = document.createElement("input");
                    accionInput.type = "hidden";
                    accionInput.name = "accion";
                    accionInput.value = "editar";
                    formulario.appendChild(accionInput);
                    formulario.submit(); // redirige a la vista de actualización según tu vista
                }, 400);
            }
        });
    }

    /* ---------- 3) clic en “Sí, continuar” de la ventana Confirmar ---------- */
    if (btnConfirmar && modalConfirmar) {
        btnConfirmar.addEventListener("click", () => {
        modalConfirmar.hide();

        /* Esperamos transición, luego modal de éxito si existe */
        setTimeout(() => {
            const accionInput = document.createElement("input");
            accionInput.type = "hidden";
            accionInput.name = "accion";
            accionInput.value = "borrar";
            formulario.appendChild(accionInput);
            formulario.submit();// <‑‑ finalmente se envía
        }, 400);
        });
    }
    });

