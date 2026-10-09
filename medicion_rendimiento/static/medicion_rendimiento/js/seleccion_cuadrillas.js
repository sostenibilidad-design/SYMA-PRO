(function () {
    "use strict";

    /* Quita y vuelve a poner una clase para que la animación CSS se repita */
    function animar(elemento, clase) {
        elemento.classList.remove(clase);
        void elemento.offsetWidth; // fuerza al navegador a "olvidar" la animación anterior
        elemento.classList.add(clase);
    }

    function quitarTildes(texto) {
        return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    }

    /* Pone la casilla de la cuadrilla y su contador según cuántos integrantes están marcados */
    function actualizarCuadrilla(grupo) {
        const casillaGrupo = grupo.querySelector(".cuadrilla-checkbox");
        const integrantes = grupo.querySelectorAll(".area-checkbox");
        const marcados = grupo.querySelectorAll(".area-checkbox:checked").length;
        const contador = grupo.querySelector(".cuadrilla-contador");

        casillaGrupo.checked = integrantes.length > 0 && marcados === integrantes.length;
        casillaGrupo.indeterminate = marcados > 0 && marcados < integrantes.length;

        const texto = `${marcados} de ${integrantes.length}`;
        if (contador && contador.textContent !== texto) {
            contador.textContent = texto;
            animar(contador, "cuadrilla-contador--salto");
        }
    }

    function inicializarCuadrillas(bloque) {
        const grupos = bloque.querySelectorAll(".cuadrilla-grupo");
        if (!grupos.length) return;

        grupos.forEach((grupo) => {
            const casillaGrupo = grupo.querySelector(".cuadrilla-checkbox");

            /* 1. Clic en la cuadrilla: marca o desmarca a todos */
            casillaGrupo.addEventListener("change", () => {
                const marcar = casillaGrupo.checked;
                grupo.querySelectorAll(".area-checkbox").forEach((casilla) => {
                    if (casilla.checked === marcar) return;
                    casilla.checked = marcar;
                    /* Avisamos el cambio para que despliegue_campos.js actualice su contador */
                    casilla.dispatchEvent(new Event("change", { bubbles: true }));
                    animar(casilla.closest(".area-item"), "cuadrilla-item--destello");
                });
                animar(casillaGrupo, "cuadrilla-checkbox--pop");
                actualizarCuadrilla(grupo);
            });

            /* 2. Clic en una persona: recalcula la casilla de su cuadrilla */
            grupo.querySelectorAll(".area-checkbox").forEach((casilla) => {
                casilla.addEventListener("change", () => actualizarCuadrilla(grupo));
            });

            /* Estado inicial (por si el formulario llega con personas ya marcadas) */
            actualizarCuadrilla(grupo);
        });

        /* 3. Buscador: también encuentra por nombre de cuadrilla y oculta cuadrillas vacías.
              Corre después del filtro por persona de despliegue_campos.js. */
        const buscador = bloque.querySelector(".input-busqueda-empleado");
        if (buscador) {
            buscador.addEventListener("input", () => {
                const texto = quitarTildes(buscador.value.trim());
                grupos.forEach((grupo) => {
                    const nombreGrupo = quitarTildes(grupo.querySelector(".cuadrilla-nombre").textContent);
                    const items = grupo.querySelectorAll(".area-item");

                    if (texto && nombreGrupo.includes(texto)) {
                        items.forEach((item) => { item.style.display = "block"; });
                        grupo.hidden = false;
                        return;
                    }
                    let alguno = false;
                    items.forEach((item) => {
                        const coincide = !texto || quitarTildes(item.textContent).includes(texto);
                        item.style.display = coincide ? "block" : "none";
                        if (coincide) alguno = true;
                    });
                    grupo.hidden = !alguno;
                });
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".funcionalidades-box--cuadrillas").forEach(inicializarCuadrillas);
    });
})();
