document.addEventListener('DOMContentLoaded', function() {
    const btnIniciarConfirmacion = document.getElementById('btn-iniciar-registro');
    const modalConfirmacion = document.getElementById('modal-confirmacion-db'); 
    const modalCalendario = document.getElementById('modal-calendario');
    const btnSiguienteCal = document.getElementById('btn-iniciar-registro-cal'); 
    
    // Festivos de Colombia: los manda el servidor (misma copia que usa el informe quincenal)
    const nodoFestivos = document.getElementById('festivos-calendario');
    const festivosColombia = nodoFestivos ? JSON.parse(nodoFestivos.textContent) : [];

    // Inicializar el Calendario Flatpickr
    const inputFecha = document.getElementById('fecha-registro');

    // Fechas que ya tienen registro: no se pueden volver a elegir
    const nodoRegistradas = document.getElementById('fechas-registradas');
    const fechasRegistradas = nodoRegistradas ? JSON.parse(nodoRegistradas.textContent) : [];
    const hoy = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().split('T')[0];

    // Nota bajo el calendario cuando hay fechas tachadas
    const zonaBotones = modalCalendario ? modalCalendario.querySelector('.botones') : null;
    if (zonaBotones && fechasRegistradas.length) {
        const nota = document.createElement('p');
        nota.className = 'nota-fechas-registradas';
        nota.textContent = 'Las fechas tachadas ya tienen un registro: solo se permite uno por fecha.';
        zonaBotones.before(nota);
    }

    if (inputFecha) {
        flatpickr("#fecha-registro", {
            inline: true,
            locale: "es",
            defaultDate: fechasRegistradas.includes(hoy) ? null : "today",
            disable: fechasRegistradas,
            onDayCreate: function(dObj, dStr, fp, dayElem) {
                const fecha = dayElem.dateObj;
                const fechaLocal = new Date(fecha.getTime() - (fecha.getTimezoneOffset() * 60000));
                const fechaString = fechaLocal.toISOString().split('T')[0];

                // Si es Domingo (0) O si está en el listado de festivos del servidor
                if (fecha.getDay() === 0 || festivosColombia.includes(fechaString)) {
                    dayElem.classList.add("dia-festivo");
                }
                if (fechasRegistradas.includes(fechaString)) {
                    dayElem.classList.add("dia-registrado");
                    dayElem.title = "Esta fecha ya tiene un registro";
                }
            }
        });
    }

    // Al hacer clic en "Base de datos al día, Iniciar" (Sincroniza Drive primero)
    if (btnIniciarConfirmacion) {
        btnIniciarConfirmacion.addEventListener('click', function() {
            const urlSync = this.getAttribute('data-url-sync');

            // Animación de carga
            const textoOriginal = this.innerHTML;
            this.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sincronizando...';
            this.disabled = true;
            this.style.opacity = '0.7';

            // Ejecutamos la extracción de Drive
            fetch(urlSync, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') 
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // ¡Éxito! Cerramos la modal de Drive y abrimos la del Calendario
                    restaurarBoton(btnIniciarConfirmacion, textoOriginal); // Por si la vuelven a abrir
                    if (modalConfirmacion) modalConfirmacion.classList.remove('active');
                    if (modalCalendario) modalCalendario.classList.add('active');
                } else {
                    alert('Error al conectar con Drive: ' + data.error);
                    restaurarBoton(btnIniciarConfirmacion, textoOriginal);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocurrió un error inesperado de red.');
                restaurarBoton(btnIniciarConfirmacion, textoOriginal);
            });
        });
    }

    // Al hacer clic en "Siguiente" dentro del Calendario (Avanza al Paso 1)
    if (btnSiguienteCal) {
        btnSiguienteCal.addEventListener('click', function() {
            const fechaElegida = inputFecha.value;
            const urlRedirect = this.getAttribute('data-url-redirect');
            
            if (!fechaElegida) {
                alert('⚠️ Por favor, selecciona una fecha.');
                return;
            }
            if (fechasRegistradas.includes(fechaElegida)) {
                alert('⚠️ Esa fecha ya tiene un registro. Solo se permite un registro por fecha.');
                return;
            }

            // Cambiamos el botón para que se vea que está avanzando
            this.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Cargando...';
            this.disabled = true;
            this.style.opacity = '0.7';

            // Redirigimos directamente al Paso 1 enviando la fecha y la página desde la que se pulsó «Registrar»,
            // para que la X del registro vuelva allí
            const origen = encodeURIComponent(window.location.pathname + window.location.search);
            window.location.href = urlRedirect + '?fecha=' + fechaElegida + '&origen=' + origen;
        });
    }

    function restaurarBoton(boton, texto) {
        boton.innerHTML = texto;
        boton.disabled = false;
        boton.style.opacity = '1';
    }
});
