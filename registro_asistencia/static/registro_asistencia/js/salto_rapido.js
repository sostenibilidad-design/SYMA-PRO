(function () {
    "use strict";

    const input = document.getElementById("rn-salto-input");
    const lista = document.getElementById("rn-salto-lista");
    const nodoConfig = document.getElementById("rn-salto-config");

    // Si la página no tiene el salto rápido (vista 5), no hacemos nada
    if (!input || !lista || !nodoConfig) return;

    const config = JSON.parse(nodoConfig.textContent);
    const MAX_SUGERENCIAS = 8;
    const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                    "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

    // "2026-10-06" → Date local (sin desfase de zona horaria)
    const [hoyA, hoyM, hoyD] = config.hoy.split("-").map(Number);
    const HOY = new Date(hoyA, hoyM - 1, hoyD);

    let sugerencias = [];
    let seleccionada = -1;

    /* ---------- Utilidades ---------- */

    // Quita tildes y pasa a minúsculas: "Miércoles" → "miercoles"
    function normalizar(texto) {
        return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
    }

    // Día 0 del mes siguiente = último día del mes actual (maneja bisiestos)
    function ultimoDia(mes, anio) {
        return new Date(anio, mes + 1, 0).getDate();
    }

    // "oct" → 9 · "sept" → 8 · mínimo 3 letras para no confundir
    function indiceMes(palabra) {
        if (palabra.length < 3) return -1;
        return MESES.findIndex(function (m) { return m.startsWith(palabra); });
    }

    // Reemplaza {anio}, {mes}, {q}, {dia} en la ruta que manda Django
    function armarUrl(plantilla, valores) {
        return plantilla.replace(/\{(\w+)\}/g, function (_, clave) { return valores[clave]; });
    }

    function capitalizar(texto) {
        return texto.charAt(0).toUpperCase() + texto.slice(1);
    }

    /* ---------- Interpretar fechas escritas ---------- */

    function interpretarFecha(texto) {
        const limpio = normalizar(texto)
            .replace(/\b(de|del)\b/g, " ")
            .replace(/[\/\-.,]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();
        if (!limpio) return null;

        let anio = null, mes = null, dia = null, q = null;
        const numeros = [];

        for (const parte of limpio.split(" ")) {
            if (/^\d{4}$/.test(parte)) anio = Number(parte);
            else if (/^[12]q$/.test(parte)) q = Number(parte[0]);
            else if (/^\d{1,2}$/.test(parte)) numeros.push(Number(parte));
            else {
                const i = indiceMes(parte);
                if (i < 0) return null;      // palabra que no es mes: no es una fecha
                mes = i;
            }
        }

        // Números sueltos: con mes escrito → es el día; sin mes → "d m" o "m aaaa"
        if (mes === null) {
            if (numeros.length === 2) { dia = numeros[0]; mes = numeros[1] - 1; }
            else if (numeros.length === 1 && anio !== null) { mes = numeros[0] - 1; }
            else if (numeros.length) return null;
        } else {
            if (numeros.length > 1) return null;
            if (numeros.length === 1) dia = numeros[0];
        }

        if (anio === null && mes === null) return null;
        if (anio === null) anio = config.anio_contexto;

        // Validaciones: año con registros, mes y día reales, nada en el futuro
        if (!config.anios.includes(anio)) return null;
        if (mes !== null && (mes < 0 || mes > 11)) return null;
        if (dia !== null && (dia < 1 || dia > ultimoDia(mes, anio))) return null;
        if (new Date(anio, mes === null ? 0 : mes, dia || 1) > HOY) return null;

        const valores = { anio: anio, mes: mes === null ? null : mes + 1, q: q, dia: dia };
        const nombreMes = mes === null ? "" : MESES[mes];

        if (dia !== null) {
            valores.q = dia <= 15 ? 1 : 2;
            return { texto: dia + " de " + nombreMes + " de " + anio, detalle: "Ir al día",
                    url: armarUrl(config.rutas.dia, valores), tipo: "fecha" };
        }
        if (q !== null) {
            return { texto: q + "Q de " + nombreMes + " de " + anio, detalle: "Ir a la quincena",
                    url: armarUrl(config.rutas.quincena, valores), tipo: "carpeta" };
        }
        if (mes !== null) {
            return { texto: capitalizar(nombreMes) + " de " + anio, detalle: "Ir al mes",
                    url: armarUrl(config.rutas.mes, valores), tipo: "carpeta" };
        }
        return { texto: String(anio), detalle: "Ir al año",
                url: armarUrl(config.rutas.anio, valores), tipo: "carpeta" };
    }

    /* ---------- Lista de sugerencias ---------- */

    function cerrarLista() {
        sugerencias = [];
        seleccionada = -1;
        lista.classList.remove("rn-salto__lista--abierta");
        input.setAttribute("aria-expanded", "false");
        input.removeAttribute("aria-activedescendant");
    }

    function pintarLista() {
        lista.replaceChildren();

        if (!sugerencias.length) {
            const vacio = document.createElement("li");
            vacio.className = "rn-salto__vacio";
            vacio.textContent = "Sin resultados";
            lista.appendChild(vacio);
        }

        sugerencias.forEach(function (opcion, i) {
            const li = document.createElement("li");
            li.id = "rn-salto-opcion-" + i;
            li.className = "rn-salto__opcion";
            li.setAttribute("role", "option");
            li.setAttribute("aria-selected", String(i === seleccionada));

            const icono = document.createElement("span");
            icono.className = "material-symbols-outlined";
            icono.setAttribute("aria-hidden", "true");
            icono.textContent = opcion.tipo === "fecha" ? "calendar_month" : "folder";

            const texto = document.createElement("b");
            texto.textContent = opcion.texto;

            const detalle = document.createElement("small");
            detalle.textContent = opcion.detalle;

            li.append(icono, texto, detalle);

            // mousedown (no click) para que ocurra antes del blur del input
            li.addEventListener("mousedown", function (e) {
                e.preventDefault();
                ir(opcion);
            });
            lista.appendChild(li);
        });

        lista.classList.add("rn-salto__lista--abierta");
        input.setAttribute("aria-expanded", "true");
        if (seleccionada >= 0) input.setAttribute("aria-activedescendant", "rn-salto-opcion-" + seleccionada);
    }

    function ir(opcion) {
        if (opcion && opcion.url) window.location.href = opcion.url;
    }

    function buscar() {
        const texto = input.value.trim();
        if (!texto) { cerrarLista(); return; }

        const termino = normalizar(texto);
        const fecha = interpretarFecha(texto);

        // Carpetas del nivel actual que coinciden, sin repetir el destino de la fecha
        const propias = config.opciones.filter(function (o) {
            const coincide = normalizar(o.texto).includes(termino) || normalizar(o.detalle).includes(termino);
            return coincide && (!fecha || o.url !== fecha.url);
        });

        sugerencias = (fecha ? [fecha] : []).concat(propias).slice(0, MAX_SUGERENCIAS);
        seleccionada = sugerencias.length ? 0 : -1;
        pintarLista();
    }

    /* ---------- Eventos ---------- */

    input.addEventListener("input", buscar);

    input.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { cerrarLista(); return; }
        if (!sugerencias.length) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            seleccionada = (seleccionada + 1) % sugerencias.length;
            pintarLista();
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            seleccionada = (seleccionada - 1 + sugerencias.length) % sugerencias.length;
            pintarLista();
        } else if (e.key === "Enter") {
            e.preventDefault();
            ir(sugerencias[seleccionada]);
        }
    });

    input.addEventListener("blur", cerrarLista);
})();
