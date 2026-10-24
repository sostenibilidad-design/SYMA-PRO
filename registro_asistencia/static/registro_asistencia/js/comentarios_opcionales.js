document.addEventListener('DOMContentLoaded', function () {
    const lista = document.getElementById('rco-lista');
    if (!lista) return;

    const vacio = document.getElementById('rco-vacio');
    const plantilla = document.getElementById('rco-plantilla');
    const mensajeError = document.getElementById('rco-error');
    const ocultos = document.getElementById('rco-ocultos');
    const contadorFooter = document.getElementById('contador-asignados');
    const contadorCaja = document.getElementById('contador-seleccionados-box');
    const checks = Array.from(document.querySelectorAll('.check-empleado'));
    const estado = JSON.parse(document.getElementById('rco-guardadas').textContent);   // { empId: { comentario, link } }
    const cajas = {};                                                                    // empId -> caja que se ve ahora
    let relleno = null;                                                                  // caja apagada mientras no hay nadie seleccionado

    function mostrarError(msg) {
        mensajeError.textContent = msg || '';
        mensajeError.hidden = !msg;
    }

    function esUrlValida(valor) {
        try {
            const url = new URL(valor);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (e) {
            return false;
        }
    }

    function filaDe(empId) {
        const check = document.querySelector('.check-empleado[value="' + empId + '"]');
        return check ? check.closest('.empleado-fila') : null;
    }

    function nombreDe(empId) {
        const fila = filaDe(empId);
        return fila ? fila.querySelector('.nombre-empleado-texto').textContent : empId;
    }

    function contar() {
        if (contadorFooter) contadorFooter.textContent = Object.keys(estado).length;
        if (contadorCaja) contadorCaja.textContent = document.querySelectorAll('.check-empleado:checked').length;
    }

    // Deja los campos ocultos de un empleado al día con lo que hay en `estado`
    function sincronizar(empId) {
        ocultos.querySelectorAll('[data-emp="' + empId + '"]').forEach(el => el.remove());
        const datos = estado[empId];
        if (datos) {
            [['comentario_', datos.comentario], ['link_del_comentario_', datos.link]].forEach(function (par) {
                const oculto = document.createElement('input');
                oculto.type = 'hidden';
                oculto.name = par[0] + empId;
                oculto.value = par[1];
                oculto.dataset.emp = empId;
                ocultos.appendChild(oculto);
            });
        }
        const fila = filaDe(empId);
        if (fila) fila.classList.toggle('rp-emp-con-datos', !!datos);
        contar();
    }

    // Crea la caja de comentario de un empleado
    function crearCaja(empId) {
        const caja = plantilla.content.firstElementChild.cloneNode(true);
        const texto = caja.querySelector('.rco-texto');
        const enlace = caja.querySelector('.rco-link__input');
        const detalles = caja.querySelector('.rco-link');
        const datos = estado[empId] || { comentario: '', link: '' };

        caja.querySelector('.rco-nombre').textContent = nombreDe(empId);
        texto.value = datos.comentario;
        enlace.value = datos.link;
        detalles.open = !!datos.link;
        texto.setAttribute('aria-label', 'Comentario para ' + nombreDe(empId));
        enlace.setAttribute('aria-label', 'Enlace de soporte para ' + nombreDe(empId));

        function guardar() {
            const comentario = texto.value.trim();
            const link = enlace.value.trim();
            if (comentario || link) estado[empId] = { comentario: comentario, link: link };
            else delete estado[empId];
            sincronizar(empId);
            if (!link || esUrlValida(link)) mostrarError('');
        }
        texto.addEventListener('input', guardar);
        enlace.addEventListener('input', guardar);
        return caja;
    }

    // Una caja por cada empleado marcado en la lista, en el orden de la lista
    function dibujar() {
        const marcados = checks.filter(c => c.checked).map(c => c.value);
        Object.keys(cajas).forEach(function (empId) {
            if (!marcados.includes(empId)) { cajas[empId].remove(); delete cajas[empId]; }
        });
        marcados.forEach(function (empId) {
            if (!cajas[empId]) cajas[empId] = crearCaja(empId);
            lista.appendChild(cajas[empId]);           // appendChild de un nodo ya puesto lo reubica: así sigue el orden de la lista
        });
        // Sin nadie seleccionado se ve una caja apagada; con selección, se retira
        if (marcados.length === 0 && !relleno) {
            relleno = plantilla.content.firstElementChild.cloneNode(true);
            relleno.classList.add('rco-item--inactivo');
            relleno.querySelector('.rco-nombre').textContent = 'Selecciona un empleado';
            relleno.querySelectorAll('textarea, input').forEach(el => { el.disabled = true; });
            lista.appendChild(relleno);
        } else if (marcados.length > 0 && relleno) {
            relleno.remove();
            relleno = null;
        }
        vacio.hidden = true;
        contar();
    }

    checks.forEach(c => c.addEventListener('change', dibujar));
    const todos = document.getElementById('check-seleccionar-todos');
    if (todos) todos.addEventListener('change', dibujar);

    // No se guarda con un enlace inválido, aunque el empleado ya no esté seleccionado
    lista.closest('form').addEventListener('submit', function (e) {
        const malo = Object.keys(estado).find(id => estado[id].link && !esUrlValida(estado[id].link));
        if (malo === undefined) return;
        e.preventDefault();
        const check = document.querySelector('.check-empleado[value="' + malo + '"]');
        if (check && !check.checked) { check.checked = true; dibujar(); }
        mostrarError('El enlace de soporte de ' + nombreDe(malo) + ' no es una URL válida (debe empezar por http:// o https://).');
    });

    Object.keys(estado).forEach(sincronizar);
    dibujar();
});
