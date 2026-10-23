document.addEventListener('DOMContentLoaded', () => {
    const contenedor = document.getElementById('rn-dias');
    const btnEliminar = document.getElementById('btn-eliminar-dias');
    const barra = document.getElementById('barra-seleccion');
    if (!contenedor || !btnEliminar || !barra) return;

    const conteo = document.getElementById('conteo-seleccion');
    const btnConfirmar = document.getElementById('btn-confirmar-eliminar');
    const btnCancelar = document.getElementById('btn-cancelar-seleccion');
    const elegidos = new Set();

    function actualizarBarra() {
        const n = elegidos.size;
        conteo.textContent = n === 1 ? '1 día seleccionado' : `${n} días seleccionados`;
        btnConfirmar.disabled = n === 0;
    }

    function activarSeleccion(activa) {
        contenedor.classList.toggle('rn-dias--seleccion', activa);
        barra.hidden = !activa;
        if (!activa) {
            elegidos.clear();
            contenedor.querySelectorAll('.rn-dia--elegido').forEach(a => a.classList.remove('rn-dia--elegido'));
        }
        actualizarBarra();
    }

    btnEliminar.addEventListener('click', () => activarSeleccion(!contenedor.classList.contains('rn-dias--seleccion')));
    btnCancelar.addEventListener('click', () => activarSeleccion(false));

    // En modo selección, la carpeta se marca en vez de abrirse
    contenedor.addEventListener('click', e => {
        if (!contenedor.classList.contains('rn-dias--seleccion')) return;
        const carpeta = e.target.closest('.rn-dia');
        if (!carpeta || !carpeta.dataset.fecha) return;   // las carpetas grises (sin registro) no se eligen
        e.preventDefault();
        const fecha = carpeta.dataset.fecha;
        if (elegidos.has(fecha)) {
            elegidos.delete(fecha);
            carpeta.classList.remove('rn-dia--elegido');
        } else {
            elegidos.add(fecha);
            carpeta.classList.add('rn-dia--elegido');
        }
        actualizarBarra();
    });

    btnConfirmar.addEventListener('click', async () => {
        if (elegidos.size === 0) return;
        if (!confirm(`¿Eliminar ${elegidos.size} día(s) con todos sus registros? Esta acción no se puede deshacer.`)) return;

        btnConfirmar.disabled = true;
        try {
            const res = await fetch(contenedor.dataset.urlEliminar, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')},
                body: JSON.stringify({fechas: Array.from(elegidos)}),
            });
            const data = await res.json();
            if (data.success) {
                window.location.reload();
            } else {
                alert(data.error || 'No se pudo eliminar.');
                btnConfirmar.disabled = false;
            }
        } catch (err) {
            alert('Error de conexión al eliminar.');
            btnConfirmar.disabled = false;
        }
    });
});
