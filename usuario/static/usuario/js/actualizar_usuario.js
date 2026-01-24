document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Script principal cargado");

    // --- ELEMENTOS PRINCIPALES ---
    const checkboxes = document.querySelectorAll('input[name="elemento"]');
    const campoOculto = document.getElementById("elemento_oculto");
    const formAccion = document.getElementById("formularioIngreso");
    const btnEliminar = document.getElementById("eliminar");
    const btnActualizar = document.getElementById("btn-actualizar");
    const modalContainer = document.getElementById("modal-container");

    let seleccionados = [];

    // --- ACTUALIZAR SELECCIÓN ---
    checkboxes.forEach(chk => {
        chk.addEventListener("change", () => {
            seleccionados = Array.from(checkboxes)
                .filter(c => c.checked)
                .map(c => c.value);
            if (campoOculto) campoOculto.value = seleccionados.join(",");
            console.log("Seleccionados:", seleccionados);
        });
    });

    // --- ELIMINAR ---
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

    // --- ACTUALIZAR ---
    if (btnActualizar) {
        btnActualizar.addEventListener("click", async e => {
            e.preventDefault();
            if (seleccionados.length !== 1) {
                alert("Selecciona exactamente un registro para actualizar.");
                return;
            }

            const userId = seleccionados[0];
            console.log("🟢 Abriendo modal para usuario:", userId);

            try {
                modalContainer.innerHTML = '<div class="loading">Cargando...</div>';

                // URL base viene desde data-url-base
                let baseUrl = btnActualizar.dataset.urlBase;
                baseUrl = baseUrl.replace(/\/$/, "").replace(/\/0$/, "");

                const resp = await fetch(`${baseUrl}/${userId}/`);
                if (!resp.ok) throw new Error("Error al cargar modal");

                const html = await resp.text();
                modalContainer.innerHTML = html;

                // --- Inicializar modal ---
                abrirModal("modal-actualizar");
                inicializarModalActualizar(modalContainer);

            } catch (err) {
                console.error("❌ Error cargando modal:", err);
                alert("No se pudo cargar la ventana de actualización.");
            }
        });
    }

    // --- FUNCIONES DEL MODAL ---
    function inicializarModalActualizar(container) {
        const formModal = container.querySelector("form");
        const areaToggle = container.querySelector("#area-toggle");
        const areaDropdown = container.querySelector("#area-dropdown");
        const funcionalidadesToggle = container.querySelector("#funcionalidades-toggle");
        const funcionalidadesDropdown = container.querySelector("#funcionalidades-dropdown");
        const areaCheckboxes = container.querySelectorAll(".area-checkbox");

        if (!formModal) {
            console.warn("⚠️ No se encontró el formulario del modal.");
            return;
        }

        // --- SUBMIT MODAL ---
        formModal.addEventListener("submit", async e => {
            e.preventDefault();
            const formData = new FormData(formModal);

            try {
                const resp = await fetch(formModal.action, {
                    method: "POST",
                    body: formData,
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                });

                if (resp.ok) {
                    alert("✅ Usuario actualizado correctamente.");
                    container.classList.add("fade-out");
                    setTimeout(() => {
                        cerrarModal("modal-actualizar");
                        document.body.classList.add("fade-body-out");
                        location.reload();
                    }, 400);
                } else {
                    alert("⚠️ Error al actualizar el usuario.");
                }
            } catch (err) {
                console.error("❌ Error al enviar actualización:", err);
                alert("Ocurrió un error al enviar los datos.");
            }
        });

        // --- DROPDOWNS ---
        const toggleDropdown = (dropdown, otherDropdown) => {
            if (!dropdown) return;
            const visible = dropdown.style.display === "block";
            dropdown.style.display = visible ? "none" : "block";
            if (otherDropdown) otherDropdown.style.display = "none";
        };

        if (areaToggle) areaToggle.addEventListener("click", e => {
            e.stopPropagation();
            toggleDropdown(areaDropdown, funcionalidadesDropdown);
        });
        if (funcionalidadesToggle) funcionalidadesToggle.addEventListener("click", e => {
            e.stopPropagation();
            toggleDropdown(funcionalidadesDropdown, areaDropdown);
        });

        document.addEventListener("click", e => {
            if (!e.target.closest(".funcionalidades-box")) {
                if (areaDropdown) areaDropdown.style.display = "none";
                if (funcionalidadesDropdown) funcionalidadesDropdown.style.display = "none";
            }
        });

        // --- SUBÁREAS ---
        areaCheckboxes.forEach(areaCb => {
            areaCb.addEventListener("change", () => {
                const areaName = areaCb.value;
                const subareas = container.querySelector(`.subareas[data-area="${areaName}"]`);
                if (subareas) {
                    subareas.style.display = areaCb.checked ? "block" : "none";
                    if (!areaCb.checked) {
                        subareas.querySelectorAll("input[type='checkbox']").forEach(cb => cb.checked = false);
                    }
                }
            });
        });

        const btnCerrar = container.querySelector(".btn-cancelar");
        if (btnCerrar) btnCerrar.addEventListener("click", e => {
            e.preventDefault();
            cerrarModal("modal-actualizar");
        });

        // --- Inicializar estado de subáreas y acciones ---
        setTimeout(() => {
            container.querySelectorAll(".area-checkbox").forEach(areaCb => {
                const areaName = areaCb.value;
                const subareas = container.querySelector(`.subareas[data-area="${areaName}"]`);
                if (areaCb.checked && subareas) {
                    subareas.style.display = "block";
                    subareas.querySelectorAll(".subarea-checkbox").forEach(subCb => {
                        const subareaName = subCb.value;
                        const acciones = container.querySelector(`.acciones[data-subarea="${subareaName}"]`);
                        if (subCb.checked && acciones) acciones.style.display = "block";
                    });
                }
            });
        }, 200);
    }

    // --- CERRAR MODAL GLOBAL ---
    window.cerrarModal = function (idModal) {
        const modal = document.getElementById(idModal);
        if (modal) {
            modal.style.display = "none";
            const form = modal.querySelector("form");
            if (form) form.reset();
        }
    };
});
