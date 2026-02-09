// 1. Envolvemos todo en un bloque { } para que las variables sean locales a este bloque
{
    // Mantenemos tus funciones originales (pueden ser declaradas así para que sean globales)
    window.abrirModal = function(idModal) {
        const modal = document.getElementById(idModal);
        if (modal) {
            modal.classList.add("active");
        }
    }

    window.inicializarModales = function(contenedor) {
        if (!contenedor) return;
        contenedor.querySelectorAll(".btn-cancelar").forEach(btn => {
            btn.addEventListener("click", () => {
                const idModal = btn.getAttribute("data-modal");
                const modal = document.getElementById(idModal);
                if (modal) modal.classList.remove("active");
            });
        });
    }

    // 2. Función para inicializar el formato de moneda de forma segura
    const iniciarFormatoMoneda = () => {
        const inputPresupuesto = document.getElementById('id_cumplimiento_presupuestal');

        // 3. VALIDACIÓN CRUCIAL: Solo ejecutar si el input existe en la página actual
        if (inputPresupuesto) {
            inputPresupuesto.addEventListener('input', function (e) {
                let value = e.target.value.replace(/\D/g, "");

                if (!value) {
                    e.target.value = "";
                    return;
                }

                const formattedValue = new Intl.NumberFormat('es-CO').format(value);
                e.target.value = `$ ${formattedValue}`;
            });
        }
    };

    // 4. Ejecutar la función inmediatamente o cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciarFormatoMoneda);
    } else {
        iniciarFormatoMoneda();
    }
}