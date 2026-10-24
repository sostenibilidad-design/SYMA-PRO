(function () {
    'use strict';

    var CLAVE = 'syma-tema';
    var TEMAS = ['claro', 'oscuro', 'sistema'];
    var ICONOS = { claro: 'light_mode', oscuro: 'dark_mode', sistema: 'contrast' };
    var raiz = document.documentElement;
    var medio = window.matchMedia('(prefers-color-scheme: dark)');

    /* localStorage puede fallar (modo privado, bloqueado): por eso el try/catch */
    function leerTema() {
        try {
            var guardado = localStorage.getItem(CLAVE);
            return TEMAS.indexOf(guardado) !== -1 ? guardado : 'sistema';
        } catch (e) {
            return 'sistema';
        }
    }

    function guardarTema(tema) {
        try { localStorage.setItem(CLAVE, tema); } catch (e) { /* sin persistencia */ }
    }

    /* "sistema" se convierte en claro u oscuro según el equipo */
    function temaReal(tema) {
        if (tema === 'sistema') return medio.matches ? 'oscuro' : 'claro';
        return tema;
    }

    function aplicarTema(tema) {
        raiz.setAttribute('data-tema', tema);
        raiz.setAttribute('data-tema-activo', temaReal(tema));
        actualizarControles(tema);
    }

    /* Botón de la barra, radios y nota de la ventana (si ya existen en el DOM) */
    function actualizarControles(tema) {
        var boton = document.getElementById('btn-tema');
        if (boton) {
            var icono = boton.querySelector('.material-symbols-outlined');
            if (icono) icono.textContent = ICONOS[tema];
            boton.setAttribute('aria-label', 'Tema: ' + tema);
        }

        var radio = document.querySelector('input[name="tema"][value="' + tema + '"]');
        if (radio) radio.checked = true;

        var nota = document.getElementById('tema-nota');
        if (nota) {
            nota.textContent = tema === 'sistema'
                ? 'Sigue la configuración de tu equipo. Ahora está en ' + temaReal(tema) + '.'
                : 'Siempre en ' + tema + ', sin importar el equipo.';
        }
    }

    /* 1. Se ejecuta de inmediato, en el <head> */
    aplicarTema(leerTema());

    /* Si la persona está en "sistema" y cambia el modo del equipo, la página lo sigue */
    medio.addEventListener('change', function () {
        var tema = raiz.getAttribute('data-tema');
        if (tema === 'sistema') aplicarTema(tema);
    });

    /* 2. La ventana se conecta cuando el HTML ya existe */
    document.addEventListener('DOMContentLoaded', function () {
        var fondo = document.getElementById('tema-fondo');
        if (!fondo) return;

        var botonQueAbrio = null;

        function abrir(boton) {
            botonQueAbrio = boton;
            fondo.hidden = false;
            boton.setAttribute('aria-expanded', 'true');
            var marcado = fondo.querySelector('input[name="tema"]:checked');
            if (marcado) marcado.focus();
        }

        function cerrar() {
            if (fondo.hidden) return;
            fondo.hidden = true;
            if (botonQueAbrio) {
                botonQueAbrio.setAttribute('aria-expanded', 'false');
                botonQueAbrio.focus(); /* el foco vuelve a donde estaba */
            }
        }

        document.querySelectorAll('[data-abrir-tema]').forEach(function (boton) {
            boton.addEventListener('click', function (e) {
                e.preventDefault();
                abrir(boton);
            });
        });

        /* El cambio se aplica apenas se elige una tarjeta */
        fondo.querySelectorAll('input[name="tema"]').forEach(function (radio) {
            radio.addEventListener('change', function () {
                aplicarTema(radio.value);
                guardarTema(radio.value);
            });
        });

        document.getElementById('tema-cerrar').addEventListener('click', cerrar);

        /* Clic en el fondo oscuro (fuera de la ventana) */
        fondo.addEventListener('click', function (e) {
            if (e.target === fondo) cerrar();
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') cerrar();
        });

        actualizarControles(raiz.getAttribute('data-tema'));
    });
})();
