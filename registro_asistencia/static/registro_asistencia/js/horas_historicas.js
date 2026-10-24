document.addEventListener('DOMContentLoaded', function () {
    const raiz = document.getElementById('rh-historicas');
    if (!raiz) return;

    const MAX = 4;
    const MIN_HORAS = 0;
    const MAX_HORAS = 24;
    const PREFIJOS = { pendientes: 'pend', deducir: 'ded' };
    const plantilla = document.getElementById('rh-plantilla');
    const ocultos = document.getElementById('rh-ocultos');
    const contadorFooter = document.getElementById('contador-asignados');
    const contadorCaja = document.getElementById('contador-seleccionados-box');
    const checks = Array.from(document.querySelectorAll('.check-empleado'));
    const guardadas = JSON.parse(document.getElementById('rh-guardadas').textContent);
    const estado = { pendientes: guardadas.pendientes || {}, deducir: guardadas.deducir || {} };   // { pestaña: { empId: [{tipo, cantidad}] } }
    const paneles = Array.from(raiz.querySelectorAll('.rh-panel'));
    const relleno = { pendientes: null, deducir: null };                                           // tarjeta apagada sin selección
    const tarjetas = { pendientes: {}, deducir: {} };                                              // tarjetas que se ven ahora
    const modeloBloque = plantilla.content.querySelector('.rh-bloque').cloneNode(true);

    /* ---------- Utilidades ---------- */

    function filaDe(empId) {
        const check = document.querySelector('.check-empleado[value="' + empId + '"]');
        return check ? check.closest('.empleado-fila') : null;
    }

    function nombreDe(empId) {
        const fila = filaDe(empId);
        return fila ? fila.querySelector('.nombre-empleado-texto').textContent : empId;
    }

    function tieneDatos(empId) {
        return Object.keys(PREFIJOS).some(tab => (estado[tab][empId] || []).length > 0);
    }

    function contar() {
        const conHoras = new Set();
        Object.keys(PREFIJOS).forEach(tab => Object.keys(estado[tab]).forEach(id => conHoras.add(id)));
        if (contadorFooter) contadorFooter.textContent = conHoras.size;
        if (contadorCaja) contadorCaja.textContent = document.querySelectorAll('.check-empleado:checked').length;
    }

    // Campos ocultos de un empleado en una pestaña (pend_tipo_ID / pend_cantidad_ID ...)
    function sincronizarOcultos(tab, empId) {
        ocultos.querySelectorAll('[data-emp="' + empId + '"][data-tab="' + tab + '"]').forEach(el => el.remove());
        (estado[tab][empId] || []).forEach(function (fila) {
            [['tipo', fila.tipo], ['cantidad', parseFloat(fila.cantidad).toFixed(2)]].forEach(function (par) {
                const oculto = document.createElement('input');
                oculto.type = 'hidden';
                oculto.name = PREFIJOS[tab] + '_' + par[0] + '_' + empId;
                oculto.value = par[1];
                oculto.dataset.emp = empId;
                oculto.dataset.tab = tab;
                ocultos.appendChild(oculto);
            });
        });
        const fila = filaDe(empId);
        if (fila) fila.classList.toggle('rp-emp-con-datos', tieneDatos(empId));
        contar();
    }

    /* ---------- Bloques "tipo + cantidad" de una tarjeta ---------- */

    function bloques(tarjeta) {
        return tarjeta.querySelectorAll('.rh-bloque');
    }

    // "N de 4 permitidos" y la barrita de 4 segmentos
    function actualizarCupo(tarjeta) {
        const n = bloques(tarjeta).length;
        tarjeta.querySelector('.rh-cupo span').textContent = n + ' de ' + MAX + ' permitidos';
        tarjeta.querySelectorAll('.rh-cupo__barra i').forEach(function (seg, i) {
            seg.classList.toggle('rh-lleno', i < n);
        });
        tarjeta.querySelector('.rh-anadir__btn').disabled = n >= MAX;
    }

    function limpiarBloque(bloque) {
        bloque.querySelector('.rh-select').selectedIndex = 0;
        bloque.querySelector('input[type="number"]').value = '0.00';
    }

    // Un empleado no puede repetir el tipo de hora: cada desplegable bloquea los tipos que ya usan los otros bloques
    function refrescarTipos(tarjeta) {
        const selects = Array.from(tarjeta.querySelectorAll('.rh-select'));
        selects.forEach(function (select) {
            const usadosPorOtros = new Set(selects.filter(s => s !== select).map(s => s.value));
            Array.from(select.options).forEach(function (op) {
                op.disabled = usadosPorOtros.has(op.value);
            });
        });
    }

    // Primer tipo que todavía no usa ningún bloque de la tarjeta
    function primerTipoLibre(tarjeta, bloque) {
        const usados = new Set(Array.from(tarjeta.querySelectorAll('.rh-select'))
            .filter(s => s !== bloque.querySelector('.rh-select')).map(s => s.value));
        const libre = Array.from(bloque.querySelector('.rh-select').options).find(op => !usados.has(op.value));
        return libre ? libre.value : null;
    }

    function mostrarError(tarjeta, msg) {
        const p = tarjeta.querySelector('.rh-error');
        p.textContent = msg || '';
        p.hidden = !msg;
    }

    // empId vacío = tarjeta de relleno (apagada) mientras no hay nadie seleccionado
    function crearTarjeta(tab, empId) {
        const tarjeta = plantilla.content.firstElementChild.cloneNode(true);
        if (!empId) {
            tarjeta.classList.add('rh-card--inactiva');
            tarjeta.querySelector('.rh-nombre').textContent = 'Selecciona un empleado';
            tarjeta.querySelectorAll('select, input, button').forEach(el => { el.disabled = true; });
            return tarjeta;
        }
        tarjeta.dataset.emp = empId;
        tarjeta.querySelector('.rh-nombre').textContent = nombreDe(empId) + ':';

        const fieldset = tarjeta.querySelector('.rh-bloques');
        tarjeta.querySelectorAll('.rh-bloque').forEach(b => b.remove());
        const filas = estado[tab][empId] || [];
        (filas.length ? filas : [null]).forEach(function (fila) {
            const bloque = modeloBloque.cloneNode(true);
            limpiarBloque(bloque);
            if (fila) {
                bloque.querySelector('.rh-select').value = fila.tipo;
                bloque.querySelector('input[type="number"]').value = parseFloat(fila.cantidad).toFixed(2);
            }
            fieldset.appendChild(bloque);
        });
        refrescarTipos(tarjeta);
        actualizarCupo(tarjeta);
        return tarjeta;
    }

    // Lo que hay en pantalla pasa al estado: solo cuentan las filas con cantidad entre 0 (sin incluir) y 24
    function guardarTarjeta(tarjeta) {
        const tab = tarjeta.closest('.rh-panel').dataset.tab;
        const empId = tarjeta.dataset.emp;
        const filas = [];
        let fueraDeRango = false;
        bloques(tarjeta).forEach(function (bloque) {
            const cantidad = parseFloat(bloque.querySelector('input[type="number"]').value);
            if (isNaN(cantidad) || cantidad === 0) return;
            if (cantidad < MIN_HORAS || cantidad > MAX_HORAS) { fueraDeRango = true; return; }
            filas.push({ tipo: bloque.querySelector('.rh-select').value, cantidad: cantidad });
        });
        mostrarError(tarjeta, fueraDeRango ? 'La cantidad debe estar entre 0 y 24 horas.' : '');
        if (filas.length) estado[tab][empId] = filas;
        else delete estado[tab][empId];
        sincronizarOcultos(tab, empId);
    }

    /* ---------- Una tarjeta por cada empleado marcado en la lista ---------- */

    function dibujar() {
        const marcados = checks.filter(c => c.checked).map(c => c.value);
        paneles.forEach(function (panel) {
            const tab = panel.dataset.tab;
            const lista = panel.querySelector('.rh-lista');
            // Sin nadie seleccionado se ve una tarjeta apagada; con selección, esa tarjeta se retira
            if (marcados.length === 0 && !relleno[tab]) {
                relleno[tab] = crearTarjeta(tab, '');
                lista.appendChild(relleno[tab]);
            } else if (marcados.length > 0 && relleno[tab]) {
                relleno[tab].remove();
                relleno[tab] = null;
            }
            Object.keys(tarjetas[tab]).forEach(function (empId) {
                if (!marcados.includes(empId)) { tarjetas[tab][empId].remove(); delete tarjetas[tab][empId]; }
            });
            marcados.forEach(function (empId) {
                if (!tarjetas[tab][empId]) tarjetas[tab][empId] = crearTarjeta(tab, empId);
                lista.appendChild(tarjetas[tab][empId]);     // reubica la tarjeta: así sigue el orden de la lista
            });
            panel.querySelector('.rh-vacio').hidden = true;
        });
        contar();
    }

    checks.forEach(c => c.addEventListener('change', dibujar));
    const todos = document.getElementById('check-seleccionar-todos');
    if (todos) todos.addEventListener('change', dibujar);

    /* ---------- Eventos de las tarjetas (delegados: sirven también para los bloques nuevos) ---------- */

    raiz.addEventListener('click', function (e) {
        const tarjeta = e.target.closest('.rh-card');
        if (!tarjeta) return;

        const flecha = e.target.closest('.rh-flechas button');
        if (flecha) {
            const entrada = flecha.closest('.rh-cantidad').querySelector('input');
            const actual = parseFloat(entrada.value) || 0;
            entrada.value = Math.min(MAX_HORAS, Math.max(MIN_HORAS, actual + parseFloat(flecha.dataset.paso))).toFixed(2);
            guardarTarjeta(tarjeta);
            return;
        }

        if (e.target.closest('.rh-anadir__btn')) {
            const existentes = bloques(tarjeta);
            if (existentes.length < MAX) {
                const nuevo = modeloBloque.cloneNode(true);
                limpiarBloque(nuevo);
                existentes[existentes.length - 1].after(nuevo);
                const libre = primerTipoLibre(tarjeta, nuevo);
                if (libre) nuevo.querySelector('.rh-select').value = libre;
                refrescarTipos(tarjeta);
                actualizarCupo(tarjeta);
                guardarTarjeta(tarjeta);
            }
            return;
        }

        const quitar = e.target.closest('.rh-quitar');
        if (quitar) {
            if (bloques(tarjeta).length > 1) quitar.closest('.rh-bloque').remove();
            else limpiarBloque(quitar.closest('.rh-bloque'));   // el último bloque no se borra, se limpia
            refrescarTipos(tarjeta);
            actualizarCupo(tarjeta);
            guardarTarjeta(tarjeta);
        }
    });

    ['input', 'change'].forEach(function (evento) {
        raiz.addEventListener(evento, function (e) {
            const tarjeta = e.target.closest('.rh-card');
            if (!tarjeta || !e.target.closest('.rh-bloque')) return;
            refrescarTipos(tarjeta);
            guardarTarjeta(tarjeta);
        });
    });

    /* ---------- Estado inicial ---------- */

    Object.keys(PREFIJOS).forEach(tab => Object.keys(estado[tab]).forEach(id => sincronizarOcultos(tab, id)));
    dibujar();
});
