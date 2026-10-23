// Animaciones de "Editar fecha de ingreso" (informe quincenal).
// No tiene lógica de negocio: solo escucha los eventos "fi:..." que lanza fecha_ingreso.js y mueve elementos
// con la Web Animations API (elemento.animate), que no deja estilos pegados al terminar.
// Si la persona pidió "reducir movimiento" en su sistema operativo, no se anima nada.
(function () {
    const sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)');
    const SUAVE = 'cubic-bezier(0.22, 1, 0.36, 1)';      // arranca rápido y frena suave

    function animar(elemento, cuadros, opciones) {
        if (!elemento || sinMovimiento.matches || !elemento.animate) return null;
        return elemento.animate(cuadros, { easing: SUAVE, ...opciones });
    }

    // Entrada en cascada: cada elemento aparece un poco después del anterior
    function cascada(elementos, cuadros, duracion, espera) {
        Array.from(elementos).forEach((el, i) => animar(el, cuadros, { duration: duracion, delay: i * espera, fill: 'backwards' }));
    }

    const SUBIR = [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }];
    const CRECER = [{ opacity: 0, transform: 'scale(0.85)' }, { opacity: 1, transform: 'none' }];

    // 1. El ícono de entrada "late" cuando se enciende, para que se note que ya se puede usar
    document.addEventListener('fi:icono-encendido', ({ detail }) => {
        animar(detail.boton, [
            { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(163, 189, 49, 0.55)' },
            { transform: 'scale(1.15)', boxShadow: '0 0 0 8px rgba(163, 189, 49, 0)', offset: 0.6 },
            { transform: 'scale(1)', boxShadow: '0 0 0 0 rgba(163, 189, 49, 0)' },
        ], { duration: 650 });
    });

    // 2. Al abrir un modal, su contenido sube en cascada (el recuadro ya trae su propia entrada en modales_campos.css)
    document.addEventListener('fi:modal-abierto', ({ detail }) => {
        const modal = detail.overlay.querySelector('.modal');
        if (!modal) return;
        const partes = modal.querySelectorAll(':scope > :not(template):not([hidden]):not(script):not(input)');
        cascada(partes, SUBIR, 320, 45);
    });

    // 3. Los días de la vista previa aparecen uno por uno
    document.addEventListener('fi:previa', ({ detail }) => {
        animar(detail.previa.firstElementChild, SUBIR, { duration: 260 });
        cascada(detail.previa.querySelectorAll('.fi-dias li'), CRECER, 240, 40);
    });

    // 4. Cambio de paso: el día entra desde la derecha al avanzar y desde la izquierda al volver.
    //    El círculo que se completa da un "salto" y la línea hacia el siguiente se llena de izquierda a derecha.
    document.addEventListener('fi:paso', ({ detail }) => {
        const { desde, hacia, circulos, contenido } = detail;
        if (desde === hacia) return;
        const lado = hacia > desde ? 24 : -24;
        animar(contenido, [{ opacity: 0, transform: `translateX(${lado}px)` }, { opacity: 1, transform: 'none' }], { duration: 300 });

        if (contenido.id === 'fi-resumen') {
            cascada(contenido.querySelectorAll('tbody tr'), SUBIR, 260, 60);
        }

        if (hacia > desde) {
            const completado = circulos[desde];
            animar(completado.querySelector('.fi-paso__numero'), [
                { transform: 'scale(1)' }, { transform: 'scale(1.25)', offset: 0.45 }, { transform: 'scale(1)' },
            ], { duration: 420 });
            animar(completado.parentElement, [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }],
                { duration: 380, pseudoElement: '::after' });
        }
        animar(circulos[hacia].querySelector('.fi-paso__numero'), [
            { boxShadow: '0 0 0 0 rgba(163, 189, 49, 0.5)' }, { boxShadow: '0 0 0 7px rgba(163, 189, 49, 0)' },
        ], { duration: 600, easing: 'ease-out' });
    });

    // 5. Paso con datos faltantes: el círculo se sacude, como un "no" con la cabeza
    document.addEventListener('fi:paso-invalido', ({ detail }) => {
        animar(detail.circulo.querySelector('.fi-paso__numero'), [
            { transform: 'translateX(0)' }, { transform: 'translateX(-5px)' }, { transform: 'translateX(5px)' },
            { transform: 'translateX(-3px)' }, { transform: 'translateX(3px)' }, { transform: 'translateX(0)' },
        ], { duration: 420, easing: 'ease-in-out' });
    });

    // 6. Al marcar "Entiendo", las filas que se van a borrar destellan en rojo y el botón rojo se asoma
    document.addEventListener('fi:entiendo', ({ detail }) => {
        if (!detail.marcado) return;
        cascada(detail.overlay.querySelectorAll('.fi-tabla tbody tr'), [
            { backgroundColor: 'rgba(164, 10, 2, 0.14)' }, { backgroundColor: 'rgba(164, 10, 2, 0)' },
        ], 700, 80);
        animar(detail.boton, [
            { transform: 'scale(1)' }, { transform: 'scale(1.06)', offset: 0.5 }, { transform: 'scale(1)' },
        ], { duration: 360 });
    });
})();
