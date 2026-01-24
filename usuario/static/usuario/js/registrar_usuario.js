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
const empleadoSelect = document.querySelector('[name="empleado"]');

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
                if (!areaCb.checked) {
                    subareas.querySelectorAll("input[type='checkbox']").forEach(cb => cb.checked = false);
                }
            }
        });
    });
});
