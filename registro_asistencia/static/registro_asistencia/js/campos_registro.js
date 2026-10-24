// Comportamiento de los campos del registro de UN empleado en UN día (componentes/ar_campos_registro.html):
// novedad, comidas, salidas múltiples y horas históricas. Lo comparten «Actualizar registro» (actualizar_registro.js)
// y el paso a paso de «Editar fecha de ingreso» (fecha_ingreso.js), para que los dos se comporten igual.
// Necesita avisos.js cargado antes (pregunta antes de borrar las salidas múltiples).
//
//   CamposRegistro.iniciar(raiz, { form, nombre, urlHabituales, elementoNovedad, claseSinAsistencia })
//     raiz               elemento que contiene los campos (el modal, o el día del paso a paso)
//     form               el <form> con los campos (form.elements['novedad'], ['hora_inicio'], ['hora_fin'])
//     nombre             nombre del empleado, para el aviso al cambiar el horario
//     urlHabituales(e,s) URL que devuelve {comidas: {tipo: [inicio, fin]}} con las comidas habituales del turno e–s
//     elementoNovedad    elemento que recibe la clase «sin asistencia» (por defecto, raiz)
//     claseSinAsistencia clase CSS que oculta lo que solo aplica a una asistencia (por defecto, la del modal)
(function () {
    // Cada botón «Añadir» va justo debajo de su zona de filas y puede tener un tope (data-max)
    function refrescarCupo(anadir) {
        const maximo = Number(anadir.dataset.max || 0);
        anadir.disabled = maximo > 0 && anadir.previousElementSibling.querySelectorAll('.ar-fila').length >= maximo;
    }

    function iniciar(raiz, opciones) {
        const { form, nombre, urlHabituales } = opciones;
        const elementoNovedad = opciones.elementoNovedad || raiz;
        const claseSinAsistencia = opciones.claseSinAsistencia || 'ar-modal--sin-asistencia';
        const novedad = form.elements['novedad'];
        const entrada = form.elements['hora_inicio'];
        const salida = form.elements['hora_fin'];
        const filasComida = Array.from(raiz.querySelectorAll('.ar-fila-comida'));
        const zonaMultiples = raiz.querySelector('.ar-multiples .ar-filas');
        const anadirMultiple = raiz.querySelector('.ar-multiples .ar-anadir');

        // Sin asistencia no hay horario, comidas ni salidas múltiples
        function aplicarNovedad() {
            elementoNovedad.classList.toggle(claseSinAsistencia, novedad.value !== 'Asistencia');
        }
        novedad.addEventListener('change', aplicarNovedad);
        aplicarNovedad();

        // Comidas: el botón ✕ borra las dos horas (no la tomó). Al cambiar el turno se rellena el horario habitual
        // de las comidas que la persona todavía no editó a mano.
        filasComida.forEach((fila) => {
            fila.querySelectorAll('input').forEach((campo) => campo.addEventListener('input', () => { fila.dataset.editada = '1'; }));
        });

        let consultaHabitual = 0;
        async function rellenarHabituales() {
            if (novedad.value !== 'Asistencia' || !entrada.value || !salida.value) return;
            const numero = ++consultaHabitual;          // solo vale la respuesta más reciente
            try {
                const respuesta = await fetch(urlHabituales(entrada.value, salida.value), { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
                if (!respuesta.ok || numero !== consultaHabitual) return;
                const { comidas } = await respuesta.json();
                filasComida.forEach((fila) => {
                    if (fila.dataset.editada) return;
                    const horario = comidas[fila.dataset.tipo] || ['', ''];
                    const [inicio, fin] = fila.querySelectorAll('input');
                    inicio.value = horario[0];
                    fin.value = horario[1];
                });
            } catch (err) { /* sin conexión: se conservan los horarios que hay */ }
        }

        // Cambiar la hora de entrada o de salida elimina las entradas y salidas múltiples: se avisa antes y,
        // si la persona cancela, el horario vuelve a como estaba
        const horarioAnterior = new Map([entrada, salida].map((campo) => [campo, campo.value]));

        function hayMultiples() {
            return Array.from(zonaMultiples.querySelectorAll('input')).some((campo) => campo.value);
        }

        async function cambioDeHorario(campo) {
            if (hayMultiples() && !await Avisos.confirmarEliminarMultiples([nombre])) {
                campo.value = horarioAnterior.get(campo);
                return false;
            }
            horarioAnterior.set(campo, campo.value);
            zonaMultiples.replaceChildren();
            refrescarCupo(anadirMultiple);
            return true;
        }

        [entrada, salida].forEach((campo) => {
            campo.addEventListener('change', async () => {
                if (await cambioDeHorario(campo)) rellenarHabituales();
            });
        });

        // Filas dinámicas: el molde de cada fila es el <template> que sigue a su botón «Añadir»
        raiz.querySelectorAll('.ar-anadir').forEach((anadir) => {
            refrescarCupo(anadir);
            anadir.addEventListener('click', () => {
                anadir.previousElementSibling.appendChild(anadir.nextElementSibling.content.cloneNode(true));
                refrescarCupo(anadir);
            });
        });

        raiz.addEventListener('click', (e) => {
            const quitar = e.target.closest('.ar-quitar');
            if (!quitar) return;
            const comida = quitar.closest('.ar-fila-comida');
            if (comida) {                                    // el ✕ de una comida solo borra sus horas
                comida.querySelectorAll('input').forEach((campo) => { campo.value = ''; });
                comida.dataset.editada = '1';
                return;
            }
            const zona = quitar.closest('.ar-filas');
            quitar.closest('.ar-fila').remove();
            if (zona && zona.nextElementSibling) refrescarCupo(zona.nextElementSibling);
        });
    }

    window.CamposRegistro = { iniciar };
})();
