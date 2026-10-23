document.addEventListener('DOMContentLoaded', function () {
    const raiz = document.getElementById('rm-multiples');
    if (!raiz) return;

    const contenedorPares = document.getElementById('rm-pares');
    const btnAnadir = document.getElementById('rm-anadir');
    const btnAsignar = document.getElementById('rm-asignar');
    const mensajeError = document.getElementById('rm-error');
    const listaConfirmados = document.querySelector('.rp-confirmed-list');
    const checkTodos = document.getElementById('check-seleccionar-todos');
    const contadorFooter = document.getElementById('contador-asignados');
    const contadorCaja = document.getElementById('contador-seleccionados-box');

    const principales = JSON.parse(document.getElementById('rm-principales').textContent);
    const guardadas = JSON.parse(document.getElementById('rm-guardadas').textContent);
    const MAX_PARES = 6;

    // Hora por defecto de un par nuevo (la misma que trae el primero)
    const MODELO = contenedorPares.querySelector('.rm-par').cloneNode(true);

    function mostrarError(texto) {
        mensajeError.textContent = texto || '';
        mensajeError.hidden = !texto;
    }

    /* ---------- Pares ---------- */

    function pares() {
        return Array.from(contenedorPares.querySelectorAll('.rm-par'));
    }

    function renumerar() {
        pares().forEach(function (par, i) {
            par.dataset.par = String(i + 1);
            par.querySelectorAll('.rm-num').forEach(n => { n.textContent = String(i + 1); });
            par.querySelector('.rm-quitar').hidden = i === 0;   // el primer par no se borra
        });
        btnAnadir.disabled = pares().length >= MAX_PARES;
    }

    function alEditar(reloj) {
        reloj.classList.remove('rc-reloj--error');
        mostrarError('');
    }

    function clonarPar() {
        const par = MODELO.cloneNode(true);
        par.querySelectorAll('.rc-reloj').forEach(r => { delete r.dataset.listo; });
        contenedorPares.appendChild(par);
        RelojPequeno.iniciar(par, alEditar);
        renumerar();
    }

    btnAnadir.addEventListener('click', function () {
        if (pares().length < MAX_PARES) clonarPar();
    });

    contenedorPares.addEventListener('click', function (e) {
        const quitar = e.target.closest('.rm-quitar');
        if (!quitar) return;
        quitar.closest('.rm-par').remove();
        renumerar();
    });

    RelojPequeno.iniciar(contenedorPares, alEditar);
    renumerar();

    /* ---------- Lectura y validación ---------- */

    // Devuelve [{salida, ingreso}] en 24 h, o null si algo está mal (y muestra el mensaje)
    function leerPares() {
        const lista = [];
        for (const par of pares()) {
            const n = par.dataset.par;
            const relojSalida = par.querySelector('.rc-reloj[data-campo="salida"]');
            const relojIngreso = par.querySelector('.rc-reloj[data-campo="ingreso"]');
            const salida = RelojPequeno.leer(relojSalida);
            const ingreso = RelojPequeno.leer(relojIngreso);

            if (!salida || !ingreso) {
                mostrarError('Par ' + n + ': la hora no es válida (use de 01:00 a 12:59).');
                (salida ? relojIngreso : relojSalida).classList.add('rc-reloj--error');
                return null;
            }
            if (ingreso <= salida) {
                mostrarError('Par ' + n + ': la hora de ingreso debe ser mayor que la de salida.');
                relojIngreso.classList.add('rc-reloj--error');
                return null;
            }
            lista.push({ salida: salida, ingreso: ingreso, par: par });
        }

        // Los pares no se pueden cruzar entre sí
        const ordenados = lista.slice().sort((a, b) => a.salida.localeCompare(b.salida));
        for (let i = 1; i < ordenados.length; i++) {
            if (ordenados[i].salida < ordenados[i - 1].ingreso) {
                mostrarError('Los pares ' + ordenados[i - 1].par.dataset.par + ' y ' + ordenados[i].par.dataset.par + ' se cruzan en el tiempo.');
                return null;
            }
        }
        return lista;
    }

    /* ---------- Chips (uno por empleado) ---------- */

    function nombreDe(empId) {
        const check = document.querySelector('.check-empleado[value="' + empId + '"]');
        return check ? check.closest('.empleado-fila').querySelector('.nombre-empleado-texto').textContent : empId;
    }

    function actualizarContadores() {
        if (contadorFooter) contadorFooter.textContent = listaConfirmados.querySelectorAll('.chip-confirmado').length;
        if (contadorCaja) contadorCaja.textContent = document.querySelectorAll('.check-empleado:checked').length;
    }

    function crearChip(empId, rangos) {
        const previo = listaConfirmados.querySelector('.chip-confirmado[data-emp="' + empId + '"]');
        if (previo) previo.remove();                  // reasignar reemplaza los pares anteriores

        const chip = document.createElement('div');
        chip.className = 'chip-confirmado';
        chip.dataset.emp = empId;
        chip.style.cssText = 'display: inline-flex; align-items: center; background: #f1f3f5; padding: 6px 12px; border-radius: 20px; margin: 5px; font-size: 14px; border: 1px solid #dee2e6;';

        const nombre = document.createElement('strong');
        nombre.textContent = nombreDe(empId);
        const detalle = document.createElement('span');
        detalle.style.color = '#666';
        detalle.textContent = '  (' + rangos.map(function (r) {
            const [salida, ingreso] = r.split('-');
            return 'Salida ' + RelojPequeno.a12h(salida) + ' / Ingreso ' + RelojPequeno.a12h(ingreso);
        }).join('; ') + ')';
        const quitar = document.createElement('i');
        quitar.className = 'fas fa-times-circle btn-quitar-chip';
        quitar.style.cssText = 'margin-left: 10px; cursor: pointer; color: #dc3545;';
        quitar.addEventListener('click', function () {
            chip.remove();
            actualizarContadores();
        });

        chip.append(nombre, detalle, quitar);
        rangos.forEach(function (rango, i) {
            const oculto = document.createElement('input');
            oculto.type = 'hidden';
            oculto.name = 'multiple__' + empId + '__' + (i + 1);
            oculto.value = rango;
            chip.appendChild(oculto);
        });
        listaConfirmados.appendChild(chip);
    }

    /* ---------- Asignar ---------- */

    btnAsignar.addEventListener('click', function () {
        mostrarError('');
        const lista = leerPares();
        if (!lista) return;

        const seleccionados = document.querySelectorAll('.check-empleado:checked');
        if (seleccionados.length === 0) {
            mostrarError('Selecciona al menos un empleado de la lista.');
            return;
        }

        // Cada hora debe quedar dentro del turno: después de la entrada y antes de la salida principal
        for (const check of seleccionados) {
            const turno = principales[check.value] || {};
            for (const p of lista) {
                if (!turno.entrada || !turno.salida || p.salida <= turno.entrada || p.ingreso >= turno.salida) {
                    mostrarError(nombreDe(check.value) + ' trabaja de ' + RelojPequeno.a12h(turno.entrada || '00:00') + ' a ' +
                        RelojPequeno.a12h(turno.salida || '00:00') + ': las horas múltiples deben quedar dentro de ese turno.');
                    p.par.querySelectorAll('.rc-reloj').forEach(r => r.classList.add('rc-reloj--error'));
                    return;
                }
            }
        }

        const rangos = lista.map(p => p.salida + '-' + p.ingreso);
        seleccionados.forEach(function (check) {
            crearChip(check.value, rangos);
            check.checked = false;
            // Hora de salida / ingreso en 24 h para el primer par (los demás viajan en los chips)
        });
        lista.forEach(function (p) {
            p.par.querySelector('input[name="hora_de_salida_multiple"]').value = p.salida;
            p.par.querySelector('input[name="hora_de_ingreso_multiple"]').value = p.ingreso;
        });
        if (checkTodos) checkTodos.checked = false;
        actualizarContadores();

        btnAsignar.classList.add('rc-btn-asignar--ok');
        setTimeout(() => btnAsignar.classList.remove('rc-btn-asignar--ok'), 900);
    });

    /* ---------- Ya guardadas en la sesión ---------- */

    Object.keys(guardadas).forEach(function (empId) {
        crearChip(empId, guardadas[empId]);
    });

    document.querySelectorAll('.check-empleado, #check-seleccionar-todos').forEach(function (el) {
        el.addEventListener('change', actualizarContadores);
    });
    actualizarContadores();
});
