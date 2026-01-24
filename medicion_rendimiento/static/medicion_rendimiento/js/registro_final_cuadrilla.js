document.addEventListener('DOMContentLoaded', () => {
    const modalId = 'modal-fin-actividad';
    const modal = document.getElementById(modalId);
    const form = modal ? modal.querySelector('form') : null;

  // Attach click listeners to each "Finalizar" button
    document.querySelectorAll('.btn-fin').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault(); // evitar acciones por defecto
            const idMedicion = btn.dataset.id || btn.getAttribute('data-id');

        if (!form) {
            console.error('No se encontró el formulario de la modal:', modalId);
            return;
        }

        // Construir action absoluto con el prefijo de la app (ajusta si tu url cambia)
        const action = `/medicion_rendimiento/registrar-fin/${idMedicion}/`;
        form.action = action;
        console.log('Modal abrir -> form.action seteado a:', form.action, 'idMedicion:', idMedicion);

        // abrir modal (añadir clase .active)
        modal.classList.add('active');
        });
    });

  // cerrar modal por botones .btn-cancelar dentro de cualquier modal
    document.querySelectorAll('.btn-cancelar').forEach(btn => {
        btn.addEventListener('click', () => {
            const idToClose = btn.getAttribute('data-modal') || 'modal-fin-actividad';
            const mod = document.getElementById(idToClose);
            if (mod) mod.classList.remove('active');
        });
    });

    // OPCIONAL: cerrar si clic fuera de la modal (overlay)
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    }
});
