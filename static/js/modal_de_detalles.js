function abrirTablaFull(btn) {
    // 1. Encontrar la tabla: El botón está dentro del mismo contenedor que la tabla
    const contenedorRelativo = btn.closest('.tabla-contenedor-relativo');
    const tablaOriginal = contenedorRelativo ? contenedorRelativo.querySelector('table') : null;
    
    // Si no encuentra el contenedor especial, intenta buscar la tabla más cercana en la sección
    const tablaFinal = tablaOriginal || document.querySelector('.tabla-scroll-wrapper table') || document.querySelector('table');

    if (tablaFinal) {
        const modal = document.getElementById('modalTablaFull');
        const destino = document.getElementById('contenedorTablaClonada');
        
        // Limpiar modal previo
        destino.innerHTML = '';

        // Clonar tabla
        const tablaClonada = tablaFinal.cloneNode(true);
        
        // Asegurar que se vea bien en el modal
        tablaClonada.style.width = '100%';
        tablaClonada.style.backgroundColor = '#fff';
        
        // Insertar en modal
        destino.appendChild(tablaClonada);
        
        // Mostrar modal
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Bloquear scroll de fondo
    } else {
        console.error("No se encontró ninguna tabla para expandir.");
    }
}

function cerrarTablaFull() {
    document.getElementById('modalTablaFull').style.display = 'none';
    document.body.style.overflow = 'auto'; // Reactivar scroll
}

// Cerrar al dar clic fuera
document.getElementById('modalTablaFull').addEventListener('click', function(e) {
    if (e.target === this) cerrarTablaFull();
});