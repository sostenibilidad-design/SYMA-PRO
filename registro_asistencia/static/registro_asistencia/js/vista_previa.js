// Vista previa (paso 5): reglas de la edición directa en la tabla.
//  1. Cambiar la hora de entrada o de salida de alguien con entradas y salidas múltiples las elimina (con aviso previo).
//  2. Quien quede con novedad «Asistencia normal» no se guarda sin hora de entrada, hora de salida y actividad.
document.addEventListener('DOMContentLoaded', () => {
    const filas = Array.from(document.querySelectorAll('tr[data-emp]'));
    if (!filas.length) return;
    const form = filas[0].closest('form');

    const campo = (fila, nombre) => fila.querySelector(`[name="final_${nombre}_${fila.dataset.emp}"]`);

    // ---- 1. Horas múltiples ----
    filas.forEach((fila) => {
        [campo(fila, 'entrada'), campo(fila, 'salida')].forEach((input) => {
            let anterior = input.value;
            input.addEventListener('change', async () => {
                if (!fila.dataset.tieneMultiples) { anterior = input.value; return; }

                if (!await Avisos.confirmarEliminarMultiples([fila.dataset.nombre])) {
                    input.value = anterior;                 // se conserva el horario y las múltiples
                    return;
                }
                anterior = input.value;
                delete fila.dataset.tieneMultiples;
                fila.querySelector('[name^="final_borrar_multiples_"]').value = '1';
                const celda = fila.querySelector('[data-celda="multiples"]');
                celda.querySelectorAll('span').forEach((s) => s.remove());
                const vacio = document.createElement('span');
                vacio.className = 'rp-prev-vacio';
                vacio.textContent = '—';
                celda.appendChild(vacio);
            });
        });
    });

    // ---- 2. Datos obligatorios de quien asiste ----
    function faltantes(fila) {
        if (campo(fila, 'novedad').value !== 'asistencia_normal') return [];
        const faltan = [];
        if (!campo(fila, 'entrada').value) faltan.push('Hora de entrada');
        if (!campo(fila, 'salida').value) faltan.push('Hora de salida');
        if (!campo(fila, 'actividad').value) faltan.push('Actividad');
        return faltan;
    }

    const campoDe = { 'Hora de entrada': 'entrada', 'Hora de salida': 'salida', 'Actividad': 'actividad' };

    function marcarFaltantes(fila, faltan) {
        faltan.forEach((nombre) => {
            const control = campo(fila, campoDe[nombre]);
            const caja = control.closest('.rp-editable-field') || control.parentElement;
            caja.classList.add('av-falta');
            control.addEventListener('input', () => caja.classList.remove('av-falta'), { once: true });
            control.addEventListener('change', () => caja.classList.remove('av-falta'), { once: true });
        });
    }

    form.addEventListener('submit', async (e) => {
        const incompletas = filas
            .map((fila) => ({ fila, nombre: fila.dataset.nombre, faltan: faltantes(fila) }))
            .filter((item) => item.faltan.length);
        if (!incompletas.length) return;

        e.preventDefault();
        document.querySelectorAll('.av-falta').forEach((c) => c.classList.remove('av-falta'));
        incompletas.forEach((item) => marcarFaltantes(item.fila, item.faltan));
        await Avisos.informacionIncompleta(incompletas);

        const primera = incompletas[0];
        const control = campo(primera.fila, campoDe[primera.faltan[0]]);
        control.scrollIntoView({ block: 'center', inline: 'center' });
        control.focus();
    });
});
