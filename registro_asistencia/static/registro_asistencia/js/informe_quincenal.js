document.addEventListener('DOMContentLoaded', function () {
    const botones = [document.getElementById('btn-informe'), document.getElementById('btn-resumen')].filter(Boolean);
    if (!botones.length) return;

    const cargando = document.getElementById('informe-cargando');
    const textoCargando = document.getElementById('texto-cargando');
    const modal = document.getElementById('modal-informe-incompleto');
    const tituloModal = document.getElementById('titulo-informe-incompleto');
    const lista = document.getElementById('lista-fechas-faltantes');
    let ocupado = false;

    function formatear(iso) {
        // Se arma con la fecha local para que no se corra un día por la zona horaria
        const [anio, mes, dia] = iso.split('-').map(Number);
        const texto = new Date(anio, mes - 1, dia).toLocaleDateString('es-CO', {
            weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric',
        });
        return texto.charAt(0).toUpperCase() + texto.slice(1);
    }

    function mostrarFaltantes(fechas, nombre) {
        tituloModal.textContent = 'No se puede generar ' + nombre;
        lista.replaceChildren();
        fechas.forEach(function (iso) {
            const li = document.createElement('li');
            li.textContent = formatear(iso);
            lista.appendChild(li);
        });
        modal.classList.add('active');
    }

    async function generar(boton) {
        if (ocupado) return;
        ocupado = true;
        const nombre = boton.dataset.nombre || 'el informe';
        textoCargando.textContent = nombre === 'el informe' ? 'Generando el informe quincenal…' : 'Generando ' + nombre + '…';
        cargando.hidden = false;
        try {
            const resp = await fetch(boton.dataset.urlValidar, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            const datos = await resp.json();
            if (datos.ok) {
                window.location.href = datos.url;   // la animación sigue hasta que cargue la página
                return;
            }
            cargando.hidden = true;
            if (datos.error) alert(datos.error);
            else mostrarFaltantes(datos.fechas || [], nombre);
        } catch (e) {
            cargando.hidden = true;
            alert('No se pudo validar la quincena. Intenta de nuevo.');
        }
        ocupado = false;
    }

    botones.forEach(function (boton) {
        boton.addEventListener('click', function () { generar(boton); });
    });
    document.getElementById('btn-cerrar-informe-incompleto').addEventListener('click', function () {
        modal.classList.remove('active');
    });

    // Si alguien llegó directo a la página con días sin registrar, se muestra el mismo aviso
    const busqueda = new URLSearchParams(window.location.search);
    botones.forEach(function (boton) {
        if (busqueda.get(boton.dataset.parametro || 'informe_incompleto') === '1') generar(boton);
    });
});
