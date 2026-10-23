// Ventanas emergentes de aviso del registro (se usan en los pasos, la vista previa y la actualización individual).
//   Avisos.confirmarEliminarMultiples(nombres) -> Promise<boolean>   «Advertencia de modificación»
//   Avisos.informacionIncompleta(items)        -> Promise            «Información incompleta», items = [{nombre, faltan: []}]
(function () {
    const SVG = 'http://www.w3.org/2000/svg';

    function icono() {
        const svg = document.createElementNS(SVG, 'svg');
        svg.setAttribute('viewBox', '0 0 64 64');
        svg.setAttribute('class', 'av-icono');
        svg.setAttribute('aria-hidden', 'true');
        const triangulo = document.createElementNS(SVG, 'path');
        triangulo.setAttribute('d', 'M32 6 L60 56 L4 56 Z');
        triangulo.setAttribute('fill', '#a40a02');
        triangulo.setAttribute('stroke', '#a40a02');
        triangulo.setAttribute('stroke-width', '6');
        triangulo.setAttribute('stroke-linejoin', 'round');
        const palito = document.createElementNS(SVG, 'rect');
        palito.setAttribute('x', '29'); palito.setAttribute('y', '22');
        palito.setAttribute('width', '6'); palito.setAttribute('height', '20');
        palito.setAttribute('rx', '3'); palito.setAttribute('fill', '#fff');
        const punto = document.createElementNS(SVG, 'circle');
        punto.setAttribute('cx', '32'); punto.setAttribute('cy', '48');
        punto.setAttribute('r', '3.5'); punto.setAttribute('fill', '#fff');
        svg.append(triangulo, palito, punto);
        return svg;
    }

    function elemento(etiqueta, clase, texto) {
        const el = document.createElement(etiqueta);
        if (clase) el.className = clase;
        if (texto !== undefined) el.textContent = texto;
        return el;
    }

    // Arma la ventana y devuelve una promesa con el botón que se pulsó (true = el principal)
    function mostrar({ titulo, parrafos, lista, principal, secundario }) {
        return new Promise((resolver) => {
            const overlay = elemento('div', 'av-overlay');
            const caja = elemento('div', 'av-caja');
            caja.setAttribute('role', 'alertdialog');
            caja.setAttribute('aria-modal', 'true');
            caja.setAttribute('aria-label', titulo);

            caja.append(icono(), elemento('h2', 'av-titulo', titulo));
            (parrafos || []).forEach((p) => {
                const parrafo = elemento('p', 'av-texto');
                if (Array.isArray(p)) {
                    p.forEach((trozo) => parrafo.append(trozo.negrita ? elemento('b', '', trozo.negrita) : document.createTextNode(trozo)));
                } else {
                    parrafo.textContent = p;
                }
                caja.appendChild(parrafo);
            });
            if (lista && lista.length) {
                const ul = elemento('ul', 'av-lista');
                lista.forEach((texto) => ul.appendChild(elemento('li', '', texto)));
                caja.appendChild(ul);
            }

            const botones = elemento('div', 'av-botones');
            const btnSecundario = secundario ? elemento('button', 'av-btn', secundario) : null;
            const btnPrincipal = elemento('button', 'av-btn av-btn--peligro', principal);
            [btnSecundario, btnPrincipal].forEach((b) => { if (b) { b.type = 'button'; botones.appendChild(b); } });
            caja.appendChild(botones);
            overlay.appendChild(caja);

            function cerrar(respuesta) {
                document.removeEventListener('keydown', alTeclear, true);
                overlay.remove();
                resolver(respuesta);
            }
            function alTeclear(e) {
                if (e.key !== 'Escape') return;
                e.stopPropagation();
                cerrar(false);
            }
            btnPrincipal.addEventListener('click', () => cerrar(true));
            if (btnSecundario) btnSecundario.addEventListener('click', () => cerrar(false));
            document.addEventListener('keydown', alTeclear, true);

            document.body.appendChild(overlay);
            (btnSecundario || btnPrincipal).focus();    // al borrar, el foco empieza en «Cancelar»
        });
    }

    window.Avisos = {
        confirmarEliminarMultiples(nombres) {
            const varios = nombres && nombres.length > 1;
            const quien = nombres && nombres.length ? [{ negrita: nombres.join(', ') }, varios ? ' ya tienen ' : ' ya tiene '] : [varios ? 'Estos empleados ya tienen ' : 'Este empleado ya tiene '];
            return mostrar({
                titulo: 'Advertencia de modificación',
                parrafos: [
                    [...quien, 'horas extras y entradas y salidas múltiples registradas. Si modificas su hora base de entrada o de salida, ' +
                        'las horas extras y entradas y salidas múltiples actuales se eliminarán permanentemente para evitar inconsistencias.'],
                    '¿Estás seguro de que deseas editar el horario base?',
                ],
                principal: 'Sí, eliminar y editar',
                secundario: 'Cancelar',
            });
        },

        informacionIncompleta(items) {
            const uno = items.length === 1;
            const intro = uno
                ? ['No es posible guardar los cambios. Faltan datos obligatorios para el empleado ', { negrita: items[0].nombre }, '.']
                : ['No es posible guardar los cambios. Faltan datos obligatorios para varios empleados.'];
            return mostrar({
                titulo: 'Información incompleta',
                parrafos: [intro, [{ negrita: 'Para continuar, por favor completa lo siguiente:' }]],
                lista: uno ? items[0].faltan : items.map((i) => `${i.nombre}: ${i.faltan.join(', ')}`),
                principal: 'Completar datos',
            });
        },
    };
})();
