// Editar la fecha de ingreso de un empleado NUEVO desde el informe quincenal.
//
// Flujo (todo dentro de #modal-container, igual que «Actualizar registro»):
//   1. Se marca UNA fila «Nuevo» del informe y se enciende el ícono #btn-fecha-ingreso.
//   2. Modal corto: la nueva fecha. Muestra qué días se agregarán o eliminarán.
//   3a. Fecha anterior  -> paso a paso (un formulario por día + resumen) y un solo POST con todos los días.
//   3b. Fecha posterior -> confirmación con «Entiendo» y un POST que borra los registros.
//
// El servidor es quien decide si la persona es nueva y valida todo otra vez; aquí solo se ayuda a quien usa la pantalla.
// Los textos dinámicos se escriben con textContent (nunca con innerHTML) y el HTML de los modales lo arma Django.
// fecha_ingreso_animaciones.js escucha los eventos «fi:...» que se lanzan desde aquí.
document.addEventListener('DOMContentLoaded', () => {
    const boton = document.getElementById('btn-fecha-ingreso');
    const contenedor = document.getElementById('modal-container');
    const tabla = document.querySelector('.inf-tabla');
    if (!boton || !contenedor || !tabla) return;

    const TITULO_BASE = 'Editar fecha de ingreso (solo empleados nuevos)';
    let abierto = false;       // solo un modal a la vez
    let guardando = false;     // mientras se envía al servidor no se puede cerrar ni repetir

    function evento(nombre, detalle) {
        document.dispatchEvent(new CustomEvent(nombre, { detail: detalle }));
    }

    function plural(cantidad, uno, varios) {
        return cantidad + ' ' + (cantidad === 1 ? uno : varios);
    }

    function crear(etiqueta, clase, texto) {
        const el = document.createElement(etiqueta);
        if (clase) el.className = clase;
        if (texto !== undefined) el.textContent = texto;
        return el;
    }

    // Token CSRF: el informe no tiene formularios, así que se lee del campo oculto de la página (o de la cookie)
    function tokenCsrf() {
        const campo = document.querySelector('#fi-csrf [name="csrfmiddlewaretoken"]');
        return (campo && campo.value) || (typeof getCookie === 'function' ? getCookie('csrftoken') : '');
    }

    // ------------------------------------------------------------------
    // 1. Ícono: solo con UNA fila marcada y que sea «Nuevo»
    // ------------------------------------------------------------------
    function actualizarIcono() {
        const marcadas = tabla.querySelectorAll('tbody tr.inf-fila-sel');
        const fila = marcadas.length === 1 ? marcadas[0] : null;
        const permitido = Boolean(fila && fila.dataset.nuevo === '1' && fila.dataset.cedula);
        const estabaApagado = boton.disabled;

        boton.disabled = !permitido;
        boton.title = fila && !permitido
            ? 'Solo se puede editar la fecha de ingreso de empleados nuevos'
            : TITULO_BASE;
        if (permitido && estabaApagado) evento('fi:icono-encendido', { boton });
    }

    // La fila se marca en el clic de la propia fila (informe_quincenal.html); este se ejecuta después, al subir el evento
    tabla.addEventListener('click', actualizarIcono);
    actualizarIcono();

    // ------------------------------------------------------------------
    // Ayudantes de los modales
    // ------------------------------------------------------------------
    function cerrar() {
        contenedor.innerHTML = '';
        abierto = false;
        guardando = false;
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && abierto && !guardando && contenedor.querySelector('.modal-overlay')) cerrar();
    });

    // Pide un modal al servidor. Si responde JSON es un error (permisos, empleado no nuevo, fecha inválida...)
    async function pedir(url) {
        const respuesta = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (respuesta.redirected) return { error: 'Tu sesión terminó. Recarga la página e inicia sesión de nuevo.' };
        if ((respuesta.headers.get('Content-Type') || '').includes('application/json')) {
            const datos = await respuesta.json().catch(() => ({}));
            return { error: datos.error || (datos.errores || [])[0] || 'No se pudo abrir.' };
        }
        if (!respuesta.ok) return { error: 'No se pudo abrir (error ' + respuesta.status + ').' };
        return { html: await respuesta.text() };
    }

    // Pone el HTML del servidor en el contenedor y arranca el comportamiento del modal que llegó
    function mostrar(html) {
        contenedor.innerHTML = html;
        const overlay = contenedor.querySelector('.modal-overlay');
        if (!overlay) { cerrar(); return; }
        overlay.classList.add('active');
        evento('fi:modal-abierto', { overlay });

        const iniciar = { corto: iniciarCorto, pasos: iniciarPasos, eliminar: iniciarEliminar }[overlay.dataset.fi];
        if (iniciar) iniciar(overlay);
        const cancelar = overlay.querySelector('#fi-cancelar');
        if (cancelar) cancelar.addEventListener('click', () => { if (!guardando) cerrar(); });
    }

    function mostrarErrores(overlay, lista) {
        const zona = overlay.querySelector('#fi-errores');
        const ul = document.createElement('ul');
        lista.forEach((texto) => ul.appendChild(crear('li', '', texto)));
        zona.replaceChildren(ul);
        zona.hidden = false;
    }

    function ocultarErrores(overlay) {
        const zona = overlay.querySelector('#fi-errores');
        if (zona) zona.hidden = true;
    }

    async function enviar(url, cuerpo) {
        const respuesta = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tokenCsrf(), 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify(cuerpo),
        });
        const datos = await respuesta.json().catch(() => ({}));
        return { ok: respuesta.ok && datos.success, datos };
    }

    // ------------------------------------------------------------------
    // Abrir desde el ícono
    // ------------------------------------------------------------------
    boton.addEventListener('click', async () => {
        if (abierto || boton.disabled) return;
        const fila = tabla.querySelector('tbody tr.inf-fila-sel');
        if (!fila || !fila.dataset.cedula) return;

        abierto = true;
        try {
            const url = boton.dataset.urlBase.replace('CEDULA', encodeURIComponent(fila.dataset.cedula));
            const respuesta = await pedir(url);
            if (respuesta.error) {
                abierto = false;
                alert(respuesta.error);
                return;
            }
            mostrar(respuesta.html);
        } catch (err) {
            abierto = false;
            alert('No se pudo abrir la edición de la fecha de ingreso.');
        }
    });

    // ------------------------------------------------------------------
    // 2. Modal corto: la nueva fecha
    // ------------------------------------------------------------------
    function iniciarCorto(overlay) {
        const form = overlay.querySelector('#fi-form-corto');
        const campo = overlay.querySelector('#fi-nueva');
        const previa = overlay.querySelector('#fi-previa');
        const continuar = overlay.querySelector('#fi-continuar');
        const dias = JSON.parse(overlay.querySelector('#fi-dias-datos').textContent);
        const actual = form.dataset.actual;

        function aviso(clase, icono, texto, etiquetas) {
            const caja = crear('div', 'fi-aviso fi-aviso--' + clase);
            caja.appendChild(crear('i', 'fa-solid ' + icono));
            const cuerpo = crear('div');
            cuerpo.appendChild(crear('span', '', texto));
            if (etiquetas.length) {
                const lista = crear('ul', 'fi-dias');
                etiquetas.forEach((t) => lista.appendChild(crear('li', '', t)));
                cuerpo.appendChild(lista);
            }
            caja.appendChild(cuerpo);
            return caja;
        }

        function actualizarPrevia() {
            ocultarErrores(overlay);
            previa.replaceChildren();
            const nueva = campo.value;
            // Las fechas ISO (AAAA-MM-DD) se comparan bien como texto
            const valida = Boolean(nueva) && nueva >= campo.min && nueva <= campo.max && nueva !== actual;
            continuar.disabled = !valida;
            if (!valida) return;

            if (nueva < actual) {
                // Solo se editan los días que ya tienen registro en el proyecto; los demás (p. ej. un domingo que nadie registró) se omiten
                const enRango = dias.filter((d) => d.iso >= nueva && d.iso < actual);
                const elegido = enRango.find((d) => d.iso === nueva);
                if (!elegido || !elegido.registrado) {
                    continuar.disabled = true;
                    previa.appendChild(aviso('peligro', 'fa-circle-exclamation',
                        'El ' + (elegido ? elegido.texto : 'día elegido') + ' no tiene registro en este proyecto, así que no se puede usar como ingreso. Elige un día con registro.', []));
                    evento('fi:previa', { previa });
                    return;
                }
                const faltan = enRango.filter((d) => d.registrado);
                const omitidos = enRango.filter((d) => !d.registrado);
                previa.appendChild(aviso('ok', 'fa-circle-plus',
                    'Se van a registrar ' + plural(faltan.length, 'día', 'días') + ' antes del ingreso actual:',
                    faltan.map((d) => d.texto + (d.habil ? '' : ' · descanso'))));
            } else {
                const sobran = dias.filter((d) => d.iso >= actual && d.iso < nueva && d.novedad);
                previa.appendChild(aviso('peligro', 'fa-trash-can',
                    'Se van a eliminar ' + plural(sobran.length, 'registro', 'registros') + ' de esta persona:',
                    sobran.map((d) => d.texto + ' · ' + d.novedad)));
            }
            evento('fi:previa', { previa });
        }

        campo.addEventListener('input', actualizarPrevia);
        campo.addEventListener('change', actualizarPrevia);
        form.addEventListener('submit', (e) => e.preventDefault());
        actualizarPrevia();

        continuar.addEventListener('click', async () => {
            continuar.disabled = true;
            try {
                const url = form.dataset.urlRevisar + '?nueva=' + encodeURIComponent(campo.value);
                const respuesta = await pedir(url);
                if (respuesta.error) {
                    mostrarErrores(overlay, [respuesta.error]);
                    continuar.disabled = false;
                    return;
                }
                mostrar(respuesta.html);
            } catch (err) {
                mostrarErrores(overlay, ['Error de conexión. Intenta de nuevo.']);
                continuar.disabled = false;
            }
        });
    }

    // ------------------------------------------------------------------
    // 3a. Paso a paso: un formulario por día y un resumen
    // ------------------------------------------------------------------
    function iniciarPasos(overlay) {
        const dias = Array.from(overlay.querySelectorAll('.fi-dia'));
        const resumen = overlay.querySelector('#fi-resumen');
        const secciones = [...dias, resumen];
        const circulos = Array.from(overlay.querySelectorAll('.fi-paso'));
        const anterior = overlay.querySelector('#fi-anterior');
        const siguiente = overlay.querySelector('#fi-siguiente');
        const guardar = overlay.querySelector('#fi-guardar');
        const nombre = overlay.querySelector('#fi-nombre').textContent;
        const ultimo = dias.length;           // posición del resumen

        let actual = 0;
        let masLejos = 0;                     // hasta dónde se ha llegado: no se salta hacia delante sin validar
        const hechos = new Set();

        function refrescar() {
            circulos.forEach((circulo, i) => {
                circulo.classList.toggle('fi-paso--actual', i === actual);
                circulo.classList.toggle('fi-paso--hecho', hechos.has(i) && i !== actual && !circulo.classList.contains('fi-paso--error'));
                circulo.disabled = i > masLejos;
            });
            anterior.disabled = actual === 0;
            siguiente.hidden = actual === ultimo;
            guardar.hidden = actual !== ultimo;
        }

        function irA(hacia) {
            if (hacia === actual || hacia < 0 || hacia > ultimo) return;
            const desde = actual;
            secciones[desde].hidden = true;
            secciones[hacia].hidden = false;
            actual = hacia;
            masLejos = Math.max(masLejos, hacia);
            if (hacia === ultimo) construirResumen();
            ocultarErrores(overlay);
            refrescar();
            evento('fi:paso', { desde, hacia, circulos, contenido: secciones[hacia] });
        }

        // --- Datos de un día ---
        function formDe(indice) {
            return dias[indice].querySelector('form');
        }

        function faltantes(indice) {
            const form = formDe(indice);
            if (form.elements['novedad'].value !== 'Asistencia') return [];
            const faltan = [];
            if (!form.elements['hora_inicio'].value) faltan.push('Hora de ingreso');
            if (!form.elements['hora_fin'].value) faltan.push('Hora de salida');
            if (!form.elements['actividad'].value) faltan.push('Actividad');
            return faltan;
        }

        // Revisión mínima en el navegador; el servidor vuelve a validar todo. Devuelve true si el día está completo.
        function diaCompleto(indice) {
            const faltan = faltantes(indice);
            const circulo = circulos[indice];
            if (faltan.length) {
                circulo.classList.add('fi-paso--error');
                if (window.Avisos) window.Avisos.informacionIncompleta([{ nombre: dias[indice].dataset.texto, faltan }]);
                evento('fi:paso-invalido', { circulo });
                return false;
            }
            if (!formDe(indice).reportValidity()) {
                circulo.classList.add('fi-paso--error');
                return false;
            }
            circulo.classList.remove('fi-paso--error');
            hechos.add(indice);
            return true;
        }

        function datosDelDia(form) {
            const datos = new FormData(form);
            const campos = {};
            new Set(datos.keys()).forEach((clave) => { campos[clave] = datos.getAll(clave); });
            return campos;
        }

        // --- Resumen ---
        function construirResumen() {
            const cuerpo = overlay.querySelector('#fi-resumen-filas');
            cuerpo.replaceChildren();
            dias.forEach((dia, i) => {
                const form = formDe(i);
                const novedad = form.elements['novedad'].value;
                const asiste = novedad === 'Asistencia';
                const fila = crear('tr');
                fila.appendChild(crear('td', '', dia.dataset.texto));
                fila.appendChild(crear('td', '', novedad));
                fila.appendChild(crear('td', 'fi-num', asiste ? form.elements['hora_inicio'].value + ' – ' + form.elements['hora_fin'].value : '--'));
                fila.appendChild(crear('td', '', asiste && form.elements['actividad'].value ? form.elements['actividad'].value : '--'));
                cuerpo.appendChild(fila);
            });
        }

        // --- Comportamiento de cada día: el mismo de «Actualizar registro» (campos_registro.js) ---
        dias.forEach((dia, i) => {
            const form = formDe(i);
            form.addEventListener('submit', (e) => e.preventDefault());
            CamposRegistro.iniciar(dia, {
                form,
                nombre,
                claseSinAsistencia: 'fi-dia--sin-asistencia',
                urlHabituales: (entrada, salida) => overlay.dataset.urlComidas + '?fecha=' + encodeURIComponent(dia.dataset.iso)
                    + '&entrada=' + encodeURIComponent(entrada) + '&salida=' + encodeURIComponent(salida),
            });
        });

        // --- Navegación ---
        circulos.forEach((circulo, i) => circulo.addEventListener('click', () => {
            if (i < actual) { irA(i); return; }                  // volver atrás siempre se puede
            if (i > actual && i <= masLejos) {                   // avanzar solo hasta donde ya se llegó, validando el día actual
                if (actual < ultimo && !diaCompleto(actual)) return;
                irA(i);
            }
        }));
        anterior.addEventListener('click', () => irA(actual - 1));
        siguiente.addEventListener('click', () => {
            if (!diaCompleto(actual)) return;
            irA(actual + 1);
        });

        // --- Guardar: un solo envío con todos los días; el servidor los valida y guarda todos o ninguno ---
        guardar.addEventListener('click', async () => {
            for (let i = 0; i < dias.length; i++) {              // revisa todos antes de enviar
                if (!diaCompleto(i)) { irA(i); return; }
            }
            guardando = true;
            guardar.disabled = true;
            ocultarErrores(overlay);
            try {
                const cuerpo = { nueva: overlay.dataset.nueva, actual: overlay.dataset.actual, dias: {} };
                dias.forEach((dia, i) => { cuerpo.dias[dia.dataset.iso] = datosDelDia(formDe(i)); });
                const { ok, datos } = await enviar(overlay.dataset.urlAgregar, cuerpo);
                if (ok) {
                    window.location.reload();
                    return;
                }
                if (Number.isInteger(datos.paso) && datos.paso >= 0 && datos.paso < dias.length) {
                    circulos[datos.paso].classList.add('fi-paso--error');
                    irA(datos.paso);
                    evento('fi:paso-invalido', { circulo: circulos[datos.paso] });
                }
                mostrarErrores(overlay, datos.errores || [datos.error || 'No se pudo guardar. Intenta de nuevo.']);
            } catch (err) {
                mostrarErrores(overlay, ['Error de conexión al guardar. No se guardó nada.']);
            }
            guardando = false;
            guardar.disabled = false;
        });

        refrescar();
        if (nombre) overlay.setAttribute('aria-label', 'Fecha de ingreso de ' + nombre);
    }

    // ------------------------------------------------------------------
    // 3b. Eliminación: confirmación con «Entiendo»
    // ------------------------------------------------------------------
    function iniciarEliminar(overlay) {
        const entiendo = overlay.querySelector('#fi-entiendo');
        const eliminar = overlay.querySelector('#fi-eliminar');

        entiendo.addEventListener('change', () => {
            eliminar.disabled = !entiendo.checked;
            evento('fi:entiendo', { marcado: entiendo.checked, overlay, boton: eliminar });
        });

        eliminar.addEventListener('click', async () => {
            if (!entiendo.checked) return;
            guardando = true;
            eliminar.disabled = true;
            ocultarErrores(overlay);
            try {
                const { ok, datos } = await enviar(overlay.dataset.urlEliminar, { nueva: overlay.dataset.nueva, actual: overlay.dataset.actual });
                if (ok) {
                    window.location.reload();
                    return;
                }
                mostrarErrores(overlay, datos.errores || [datos.error || 'No se pudo eliminar. Intenta de nuevo.']);
            } catch (err) {
                mostrarErrores(overlay, ['Error de conexión. No se eliminó nada.']);
            }
            guardando = false;
            eliminar.disabled = !entiendo.checked;
        });
    }
});
