document.addEventListener('DOMContentLoaded', () => {
    
    // --- LÓGICA DEL CLIMA ---
    function setupWeatherGroup(groupId) {
        const group = document.getElementById(groupId);
        if (!group) return;

        const buttons = group.querySelectorAll('.bt-w-btn');
        const hiddenInput = group.querySelector('input[type="hidden"]');

        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Quita la clase 'active' a todos los de este grupo
                buttons.forEach(b => b.classList.remove('active'));
                // Añade la clase al que se hizo clic
                btn.classList.add('active');
                // Pasa el valor oculto a Django
                hiddenInput.value = btn.getAttribute('data-value');
            });
        });
    }

    setupWeatherGroup('clima-manana');
    setupWeatherGroup('clima-tarde');

});

// --- LÓGICA DE LOS CONTADORES (Por fuera del DOMContentLoaded para usar en onclick) ---
function updateCount(inputId, change) {
    const input = document.getElementById(inputId);
    let currentValue = parseInt(input.value) || 0;
    
    // Suma o resta, pero no permite que baje de cero
    let newValue = currentValue + change;
    if (newValue < 0) newValue = 0;
    
    input.value = newValue;
}

// --- MOTOR DE AUTOGUARDADO ---
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form-bitacora');
    const inputIdBitacora = document.getElementById('id_bitacora');
    let timeoutId;

    // Detectar cualquier entrada de texto o cambio
    form.addEventListener('input', manejarAutoGuardado);
    form.addEventListener('change', manejarAutoGuardado);

    function manejarAutoGuardado(e) {
        // Ignorar si lo que cambió fue un archivo (fotos/firmas se manejan aparte)
        if (e.target.type === 'file') return;

        // Esperar 1.5 segundos de inactividad antes de golpear el servidor (Debounce)
        clearTimeout(timeoutId);
        timeoutId = setTimeout(enviarDatos, 1500);
    }

    async function enviarDatos() {
        // Extraer el ID del proyecto de la URL actual
        const urlParams = window.location.pathname.split('/');
        const idProyecto = urlParams[urlParams.indexOf('proyecto') + 1];
        
        const formData = new FormData(form);

        try {
            // Reemplaza esto con tu forma de obtener el CSRF Token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            const response = await fetch(`/bitacora/api/autosave/${idProyecto}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            });

            const data = await response.json();
            if (data.status === 'success') {
                console.log("✅ Auto-guardado exitoso. ID:", data.id_bitacora);
                // Si era una nueva entrada, inyectamos el nuevo ID para que siga actualizando el mismo registro
                if (!inputIdBitacora.value) {
                    inputIdBitacora.value = data.id_bitacora;
                    // Opcional: Actualizar la URL sin recargar la página para que quede en modo edición
                    window.history.replaceState({}, '', `/bitacora/proyecto/${idProyecto}/${data.id_bitacora}/`);
                }
            }
        } catch (error) {
            console.error("❌ Error en auto-guardado:", error);
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    
    // --- 1. LÓGICA DE FLECHAS DEL CARRUSEL ---
    const container = document.getElementById('photo-container');
    const btnPrev = document.getElementById('btn-prev-photo');
    const btnNext = document.getElementById('btn-next-photo');

    if(btnPrev && container) {
        btnPrev.addEventListener('click', () => {
            // Retrocede exactamente una foto (80px) + el gap (10px) = 90px
            container.scrollBy({ left: -90, behavior: 'smooth' });
        });
    }
    if(btnNext && container) {
        btnNext.addEventListener('click', () => {
            // Avanza exactamente una foto
            container.scrollBy({ left: 90, behavior: 'smooth' });
        });
    }

    // --- 2. SUBIDA INSTANTÁNEA DE FOTOS ---
    const inputFotos = document.getElementById('input-fotos');
    if (inputFotos) {
        inputFotos.addEventListener('change', async function(e) {
            const files = e.target.files;
            if (files.length === 0) return;
            
            const inputIdBitacora = document.getElementById('id_bitacora');
            if (!inputIdBitacora.value) {
                alert("Por favor, ingresa al menos la fecha o un dato inicial para crear la bitácora antes de subir fotos.");
                inputFotos.value = ''; // Limpiar selección
                return;
            }

            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('fotos', files[i]);
            }
            
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const spanIcon = document.getElementById('span-add-icon');
            
            // Icono de cargando...
            spanIcon.innerHTML = '⏳';

            try {
                const response = await fetch(`/bitacora/api/upload_fotos/${inputIdBitacora.value}/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    }
                });
                
                const data = await response.json();
                if (data.status === 'success') {
                    // Inyectar las nuevas fotos en el HTML antes del botón +
                    const labelAdd = document.getElementById('label-add-photo');
                    data.fotos.forEach(foto => {
                        const div = document.createElement('div');
                        div.className = 'bt-photo-thumb';
                        div.id = `foto-${foto.id}`;
                        div.innerHTML = `
                            <img src="${foto.url}" alt="Foto bitácora">
                            <button type="button" class="btn-delete-photo" onclick="eliminarFoto(${foto.id})">×</button>
                        `;
                        container.insertBefore(div, labelAdd);
                    });
                    
                    // Hacer scroll automático hacia la derecha para ver las nuevas fotos
                    container.scrollLeft = container.scrollWidth;
                }
            } catch (error) {
                console.error("Error subiendo fotos:", error);
            } finally {
                // Restaurar botón y vaciar input
                spanIcon.innerHTML = '+';
                inputFotos.value = '';
            }
        });
    }
});

// --- 3. ELIMINAR FOTO POR AJAX ---
async function eliminarFoto(idFoto) {
    if(!confirm('¿Seguro que deseas eliminar esta foto?')) return;
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
        const response = await fetch(`/bitacora/api/delete_foto/${idFoto}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            }
        });
        
        const data = await response.json();
        if(data.status === 'success') {
            const fotoDiv = document.getElementById(`foto-${idFoto}`);
            if(fotoDiv) fotoDiv.remove(); // Desaparece del DOM
        }
    } catch (error) {
        console.error("Error eliminando foto:", error);
    }
}

// --- ANIMACIÓN DE PASAR PÁGINA (FLIPBOOK 3D) ---
function turnPage(url, direction) {
    const pageRight = document.querySelector('.bt-page-right');
    const pageLeft = document.querySelector('.bt-page-left');

    // Levantamos y giramos la hoja correspondiente
    if (direction === 'next' && pageRight) {
        pageRight.classList.add('flip-next');
    } else if (direction === 'prev' && pageLeft) {
        pageLeft.classList.add('flip-prev');
    }

    // Esperamos 600ms a que termine el giro para cargar la nueva hoja
    setTimeout(() => {
        window.location.href = url;
    }, 600); 
}