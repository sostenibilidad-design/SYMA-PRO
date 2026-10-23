// Alternar entre modo manual / selección
const modoManual = document.getElementById('modo-manual');
const modoSeleccion = document.getElementById('modo-seleccion');
const manualFields = document.getElementById('manual-fields');
const seleccionFields = document.getElementById('seleccion-fields');

// Campos del modo manual
const nombreInput = document.querySelector('[name="nombre_completo"]');
const cedulaInput = document.querySelector('[name="cedula"]');
const cargoInput = document.querySelector('[name="cargo"]');

// Campo del modo selección
const empleadoSelect = document.getElementById('empleado-valor');

modoManual.addEventListener('change', () => {
    // Mostrar campos manuales
    manualFields.style.display = 'block';
    seleccionFields.style.display = 'none';

    // Hacer obligatorios los manuales
    nombreInput.required = true;
    cedulaInput.required = true;
    cargoInput.required = true;

    // Quitar required al select
    empleadoSelect.required = false;
});

modoSeleccion.addEventListener('change', () => {
    // Mostrar campos de selección
    manualFields.style.display = 'none';
    seleccionFields.style.display = 'block';

    // Quitar required de los manuales
    nombreInput.required = false;
    cedulaInput.required = false;
    cargoInput.required = false;

    // Hacer obligatorio el select
    empleadoSelect.required = true;
});

// 🔹 Mostrar/ocultar subáreas según área seleccionada
document.addEventListener("DOMContentLoaded", () => {
    const areaToggle = document.getElementById("area-toggle");
    const areaDropdown = document.getElementById("area-dropdown");
    const funcionalidadesToggle = document.getElementById("funcionalidades-toggle");
    const funcionalidadesDropdown = document.getElementById("funcionalidades-dropdown");

    const areaCheckboxes = document.querySelectorAll(".area-checkbox");

    // --- Mostrar/ocultar los dropdowns ---
    const toggleDropdown = (dropdown, otherDropdown) => {
        const visible = dropdown.style.display === "block";
        dropdown.style.display = visible ? "none" : "block";
        if (otherDropdown) otherDropdown.style.display = "none";
    };

    areaToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleDropdown(areaDropdown, funcionalidadesDropdown);
    });

    funcionalidadesToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        toggleDropdown(funcionalidadesDropdown, areaDropdown);
    });

    // --- Cerrar al hacer clic fuera ---
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".funcionalidades-box")) {
            areaDropdown.style.display = "none";
            funcionalidadesDropdown.style.display = "none";
        }
    });

    // --- Mostrar subáreas según las áreas seleccionadas ---
    areaCheckboxes.forEach(areaCb => {
        areaCb.addEventListener("change", () => {
            const areaName = areaCb.value;
            const subareas = document.querySelector(`.subareas[data-area="${areaName}"]`);

            if (subareas) {
                subareas.style.display = areaCb.checked ? "block" : "none";
                // Marcar el área selecciona todas sus subáreas y acciones; desmarcarla las limpia
                subareas.querySelectorAll("input[type='checkbox']").forEach(cb => cb.checked = areaCb.checked);
            }
        });
    });
});


// 🔹 Selector de empleado con buscador (una sola opción)
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("empleado-toggle");
    const dropdown = document.getElementById("empleado-dropdown");
    const texto = document.getElementById("empleado-texto");
    const valor = document.getElementById("empleado-valor");
    const buscador = document.getElementById("empleado-busqueda");
    const opciones = document.querySelectorAll(".empleado-opcion");
    const form = document.querySelector("form.form");

    if (!toggle || !dropdown) return;

    toggle.addEventListener("click", (e) => {
        e.stopPropagation();
        const abierto = dropdown.style.display === "block";
        dropdown.style.display = abierto ? "none" : "block";
        if (!abierto) buscador.focus();
    });

    buscador.addEventListener("click", (e) => e.stopPropagation());

    buscador.addEventListener("input", () => {
        const termino = buscador.value.toLowerCase().trim();
        opciones.forEach(op => {
            op.style.display = op.textContent.toLowerCase().includes(termino) ? "block" : "none";
        });
    });

    opciones.forEach(op => {
        op.addEventListener("click", () => {
            opciones.forEach(o => o.classList.remove("seleccionado"));
            op.classList.add("seleccionado");
            valor.value = op.dataset.valor;
            texto.textContent = op.textContent.trim();
            dropdown.style.display = "none";
        });
    });

    document.addEventListener("click", (e) => {
        if (!e.target.closest("#box-empleado")) dropdown.style.display = "none";
    });

    // El campo oculto no se valida solo: exigimos empleado en el modo "seleccionar de la lista"
    form.addEventListener("submit", (e) => {
        if (modoSeleccion.checked && !valor.value) {
            e.preventDefault();
            alert("Selecciona un empleado de la lista.");
        }
    });
});
