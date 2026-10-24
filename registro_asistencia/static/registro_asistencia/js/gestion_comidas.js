document.addEventListener('DOMContentLoaded', function () {
    const columnas = document.getElementById('rc-gestion-comidas');
    if (!columnas) return;

    const listaConfirmados = document.querySelector('.rp-confirmed-list');
    const checkTodos = document.getElementById('check-seleccionar-todos');
    const contadorFooter = document.getElementById('contador-asignados');
    const contadorCaja = document.getElementById('contador-seleccionados-box');
    const mensajeError = document.getElementById('rc-error');
    const NOMBRES = { desayuno: 'Desayuno', almuerzo: 'Almuerzo', cena: 'Cena' };

    function mostrarError(texto) {
        mensajeError.textContent = texto || '';
        mensajeError.hidden = !texto;
    }

    /* ---------- Relojes ---------- */

    RelojPequeno.iniciar(columnas, function (reloj) {
        reloj.classList.remove('rc-reloj--error');
        mostrarError('');
    });

    /* ---------- Interruptor "Habilitar ..." ---------- */

    columnas.querySelectorAll('.rc-comida').forEach(function (seccion) {
        const interruptor = seccion.querySelector('.rc-switch__input');
        const boton = seccion.querySelector('.rc-btn-asignar');

        function sincronizar() {
            seccion.classList.toggle('rc-comida--off', !interruptor.checked);
            boton.disabled = !interruptor.checked;
        }
        interruptor.addEventListener('change', sincronizar);
        sincronizar();

        boton.addEventListener('click', function () {
            asignar(seccion);
        });
    });

    /* ---------- Chips (uno por empleado y comida) ---------- */

    function nombreDe(empId) {
        const check = document.querySelector('.check-empleado[value="' + empId + '"]');
        return check ? check.closest('.empleado-fila').querySelector('.nombre-empleado-texto').textContent : empId;
    }

    function actualizarContadores() {
        const conComida = new Set(
            Array.from(listaConfirmados.querySelectorAll('.chip-confirmado')).map(c => c.dataset.emp)
        );
        if (contadorFooter) contadorFooter.textContent = conComida.size;
        if (contadorCaja) contadorCaja.textContent = document.querySelectorAll('.check-empleado:checked').length;
    }

    function crearChip(empId, tipo, rango) {
        const previo = listaConfirmados.querySelector('.chip-confirmado[data-emp="' + empId + '"][data-tipo="' + tipo + '"]');
        if (previo) previo.remove();                  // reasignar reemplaza la comida anterior

        const [inicio, fin] = rango.split('-');
        const chip = document.createElement('div');
        chip.className = 'chip-confirmado';
        chip.dataset.emp = empId;
        chip.dataset.tipo = tipo;
        chip.style.cssText = 'display: inline-flex; align-items: center; background: #f1f3f5; padding: 6px 12px; border-radius: 20px; margin: 5px; font-size: 14px; border: 1px solid #dee2e6;';

        const nombre = document.createElement('strong');
        nombre.textContent = nombreDe(empId);
        const detalle = document.createElement('span');
        detalle.style.color = '#666';
        detalle.textContent = '  (' + NOMBRES[tipo] + ': ' + RelojPequeno.a12h(inicio) + ' - ' + RelojPequeno.a12h(fin) + ')';
        const quitar = document.createElement('i');
        quitar.className = 'fas fa-times-circle btn-quitar-chip';
        quitar.style.cssText = 'margin-left: 10px; cursor: pointer; color: #dc3545;';
        const oculto = document.createElement('input');
        oculto.type = 'hidden';
        oculto.name = 'comida__' + empId + '__' + tipo;
        oculto.value = rango;

        quitar.addEventListener('click', function () {
            chip.remove();
            actualizarContadores();
        });

        chip.append(nombre, detalle, quitar, oculto);
        listaConfirmados.appendChild(chip);
    }

    function asignar(seccion) {
        const tipo = seccion.dataset.comida;
        const relojInicio = seccion.querySelector('.rc-reloj[data-campo="inicio"]');
        const relojFin = seccion.querySelector('.rc-reloj[data-campo="fin"]');
        const inicio = RelojPequeno.leer(relojInicio);
        const fin = RelojPequeno.leer(relojFin);

        relojInicio.classList.remove('rc-reloj--error');
        relojFin.classList.remove('rc-reloj--error');

        if (!inicio || !fin) {
            mostrarError(NOMBRES[tipo] + ': la hora no es válida (use de 01:00 a 12:59).');
            (inicio ? relojFin : relojInicio).classList.add('rc-reloj--error');
            return;
        }
        if (fin <= inicio) {
            mostrarError(NOMBRES[tipo] + ': la hora de finalización debe ser mayor que la de inicio.');
            relojFin.classList.add('rc-reloj--error');
            return;
        }

        const seleccionados = document.querySelectorAll('.check-empleado:checked');
        if (seleccionados.length === 0) {
            mostrarError('Selecciona al menos un empleado de la lista.');
            return;
        }

        mostrarError('');
        seleccionados.forEach(function (check) {
            crearChip(check.value, tipo, inicio + '-' + fin);
            check.checked = false;
        });
        if (checkTodos) checkTodos.checked = false;
        actualizarContadores();

        const boton = seccion.querySelector('.rc-btn-asignar');
        boton.classList.add('rc-btn-asignar--ok');
        setTimeout(() => boton.classList.remove('rc-btn-asignar--ok'), 900);
    }

    /* ---------- Comidas ya guardadas en la sesión ---------- */

    const nodoGuardadas = document.getElementById('rc-guardadas');
    const guardadas = nodoGuardadas ? JSON.parse(nodoGuardadas.textContent) : {};
    Object.keys(guardadas).forEach(function (empId) {
        Object.keys(guardadas[empId]).forEach(function (tipo) {
            crearChip(empId, tipo, guardadas[empId][tipo]);
        });
    });

    document.querySelectorAll('.check-empleado, #check-seleccionar-todos').forEach(function (el) {
        el.addEventListener('change', actualizarContadores);
    });
    actualizarContadores();
});
