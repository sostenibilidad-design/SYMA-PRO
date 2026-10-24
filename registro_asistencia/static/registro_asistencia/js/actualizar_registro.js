document.addEventListener('DOMContentLoaded', () => {
    const boton = document.getElementById('btn-actualizar-registro');
    const contenedor = document.getElementById('modal-container');
    if (!boton || !contenedor) return;

    const casillas = Array.from(document.querySelectorAll('input[name="elemento"]'));
    let abierto = false;       // solo se permite una actualización a la vez

    // Una sola fila marcada a la vez
    casillas.forEach((casilla) => {
        casilla.addEventListener('change', () => {
            if (!casilla.checked) return;
            casillas.forEach((otra) => { if (otra !== casilla) otra.checked = false; });
        });
    });

    function cerrar() {
        contenedor.innerHTML = '';
        abierto = false;
    }

    boton.addEventListener('click', async (e) => {
        e.preventDefault();
        if (abierto) return;

        const marcadas = casillas.filter((c) => c.checked);
        if (marcadas.length !== 1) {
            alert('Selecciona exactamente un registro para actualizar.');
            return;
        }

        abierto = true;
        try {
            const url = boton.dataset.urlBase.replace(/0\/actualizar\/$/, marcadas[0].value + '/actualizar/');
            const respuesta = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            if (!respuesta.ok) throw new Error('HTTP ' + respuesta.status);
            contenedor.innerHTML = await respuesta.text();
            iniciarModal(contenedor.querySelector('#modal-actualizar-registro'));
        } catch (err) {
            abierto = false;
            alert('No se pudo abrir el registro para actualizar.');
        }
    });

    function iniciarModal(overlay) {
        const modal = overlay.querySelector('.ar-modal');
        const form = overlay.querySelector('#form-actualizar-registro');
        const errores = overlay.querySelector('#ar-errores');
        const botones = overlay.querySelector('#ar-botones');
        const confirmacion = overlay.querySelector('#ar-confirmacion');
        const btnConfirmar = overlay.querySelector('#ar-confirmar');

        overlay.classList.add('active');
        const novedad = form.elements['novedad'];
        const entrada = form.elements['hora_inicio'];
        const salida = form.elements['hora_fin'];
        const novedadInicial = novedad.value;
        const nombreEmpleado = overlay.querySelector('.ar-persona strong').textContent;

        // Novedad, comidas, salidas múltiples y horas históricas: el mismo comportamiento que en «Editar fecha de ingreso»
        CamposRegistro.iniciar(overlay, {
            form,
            nombre: nombreEmpleado,
            urlHabituales: (ingreso, fin) => form.dataset.url + '?habituales=1&entrada=' + ingreso + '&salida=' + fin,
            elementoNovedad: modal,
        });

        function mostrarErrores(lista) {
            const ul = document.createElement('ul');
            lista.forEach((texto) => {
                const li = document.createElement('li');
                li.textContent = texto;
                ul.appendChild(li);
            });
            errores.replaceChildren(ul);
            errores.hidden = false;
        }

        function pasoConfirmacion(activo) {
            confirmacion.hidden = !activo;
            botones.hidden = activo;
            modal.classList.toggle('ar-modal--confirmando', activo);
        }

        overlay.querySelector('#ar-cancelar').addEventListener('click', cerrar);
        overlay.querySelector('#ar-volver').addEventListener('click', () => pasoConfirmacion(false));

        // Quien pasa a Asistencia necesita los datos de los pasos obligatorios: ingreso, salida y actividad
        function datosFaltantes() {
            if (novedad.value !== 'Asistencia') return [];
            const faltan = [];
            if (!entrada.value) faltan.push('Hora de ingreso');
            if (!salida.value) faltan.push('Hora de salida');
            if (novedadInicial !== 'Asistencia' && !form.elements['actividad'].value) faltan.push('Actividad');
            return faltan;
        }

        // 1) Guardar cambios -> pide confirmación (revisión mínima en el navegador)
        overlay.querySelector('#ar-guardar').addEventListener('click', () => {
            errores.hidden = true;
            const faltan = datosFaltantes();
            if (faltan.length) {
                Avisos.informacionIncompleta([{ nombre: nombreEmpleado, faltan }]);
                return;
            }
            if (!form.reportValidity()) return;
            pasoConfirmacion(true);
        });

        // 2) Confirmar -> el servidor valida, guarda y recalcula
        btnConfirmar.addEventListener('click', async () => {
            btnConfirmar.disabled = true;
            try {
                const respuesta = await fetch(form.dataset.url, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: new FormData(form),
                });
                const datos = await respuesta.json().catch(() => ({}));
                if (respuesta.ok && datos.success) {
                    window.location.reload();
                    return;
                }
                pasoConfirmacion(false);
                mostrarErrores(datos.errores || ['No se pudo actualizar el registro.']);
            } catch (err) {
                pasoConfirmacion(false);
                mostrarErrores(['Error de conexión al actualizar.']);
            }
            btnConfirmar.disabled = false;
        });
    }
});
