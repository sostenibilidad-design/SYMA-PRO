document.addEventListener('DOMContentLoaded', () => {
    const modalFirmas = document.getElementById('modal-firmas');
    const btnAbrirFirmas = document.getElementById('btn-abrir-firmas');
    const btnCancelar = document.querySelector('#modal-firmas .btn-cancelar');

    // --- 1. ABRIR MODAL Y CARGAR CANVAS ---
    if (btnAbrirFirmas && modalFirmas) {
        btnAbrirFirmas.addEventListener('click', (e) => {
            e.preventDefault();
            // Mostrar la modal
            modalFirmas.classList.add('active'); 
            modalFirmas.style.display = 'flex'; // Forzamos el display por si acaso

            // Esperar 200ms a que la animación termine para que el canvas tenga tamaño real
            setTimeout(() => {
                iniciarCanvas('canvas-autor', 'placeholder-autor');
                iniciarCanvas('canvas-supervisor', 'placeholder-supervisor');
            }, 200); 
        });
    }

    // --- 2. CERRAR MODAL ---
    if (btnCancelar && modalFirmas) {
        btnCancelar.addEventListener('click', (e) => {
            e.preventDefault();
            modalFirmas.classList.remove('active');
            modalFirmas.style.display = 'none';
        });
    }

    // ==========================================
    // 3. ENVÍO DE FIRMAS POR AJAX
    // ==========================================
    const formFirmas = document.getElementById('form-firmas');
    if (formFirmas) {
        formFirmas.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 1. Extraemos el ID de la bitácora que está abierta en el cuaderno
            const idBitacoraMain = document.getElementById('id_bitacora');
            if (!idBitacoraMain || !idBitacoraMain.value) {
                alert("Debes llenar algún dato (ej: Clima) para que la bitácora se cree antes de poder firmarla.");
                return;
            }
            document.getElementById('id_bitacora_firma').value = idBitacoraMain.value;

            // 🔥 SOLUCIÓN AQUÍ: Solo intentamos extraer el canvas si el input existe en el HTML
            const inputAutor = document.getElementById('firma_dibujada_autor');
            const inputSupervisor = document.getElementById('firma_dibujada_supervisor');

            if (inputAutor) {
                inputAutor.value = obtenerImagenCanvas('canvas-autor');
            }
            if (inputSupervisor) {
                inputSupervisor.value = obtenerImagenCanvas('canvas-supervisor');
            }

            // Enviamos por Fetch API
            const formData = new FormData(formFirmas);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const urlParams = window.location.pathname.split('/');
            const idProyecto = urlParams[urlParams.indexOf('proyecto') + 1];
            
            const btnSubmit = formFirmas.querySelector('.btn-guardar');
            const textoOriginal = btnSubmit.innerHTML;
            btnSubmit.innerHTML = "Guardando firmas...";
            btnSubmit.disabled = true;

            try {
                const response = await fetch(`/bitacora/api/guardar_firmas/${idProyecto}/`, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken }
                });

                const data = await response.json();
                if (data.status === 'success') {
                    alert("¡Firmas guardadas exitosamente!");
                    window.location.reload(); // Recarga para aplicar los cambios
                } else {
                    alert("Error: " + data.message);
                }
            } catch (error) {
                console.error("Error enviando firmas:", error);
                alert("Hubo un error de conexión.");
            } finally {
                btnSubmit.innerHTML = textoOriginal;
                btnSubmit.disabled = false;
            }
        });
    }

    // --- 4. OCULTAR PLACEHOLDER AL SUBIR ARCHIVO ---
    const fileAutor = document.getElementById('file_autor');
    const fileSupervisor = document.getElementById('file_supervisor');
    
    if(fileAutor) fileAutor.addEventListener('change', () => ocultarPlaceholder('placeholder-autor'));
    if(fileSupervisor) fileSupervisor.addEventListener('change', () => ocultarPlaceholder('placeholder-supervisor'));
});

// ==========================================
// LÓGICA DE DIBUJO EN CANVAS
// ==========================================

function iniciarCanvas(canvasId, placeholderId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    // Ajustar resolución interna al tamaño CSS visual (Evita desfase del ratón)
    const rect = canvas.parentElement.getBoundingClientRect();
    if (rect.width === 0) return; // Si sigue oculto, abortar para no dañar el lienzo
    
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext('2d');
    const placeholder = document.getElementById(placeholderId);
    
    let dibujando = false;

    // Estilo del lapicero
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#1a252f"; // Azul muy oscuro/negro

    // Eventos Mouse (PC)
    canvas.addEventListener('mousedown', iniciarTrazo);
    canvas.addEventListener('mousemove', dibujar);
    canvas.addEventListener('mouseup', detenerTrazo);
    canvas.addEventListener('mouseout', detenerTrazo);

    // Eventos Touch (Móviles)
    canvas.addEventListener('touchstart', iniciarTrazo, {passive: false});
    canvas.addEventListener('touchmove', dibujar, {passive: false});
    canvas.addEventListener('touchend', detenerTrazo);

    function iniciarTrazo(e) {
        e.preventDefault(); // Evita scroll en móviles al dibujar
        dibujando = true;
        if(placeholder) placeholder.style.display = 'none';
        canvas.setAttribute('data-dibujado', 'true');
        
        ctx.beginPath();
        const pos = obtenerPosicion(e, canvas);
        ctx.moveTo(pos.x, pos.y);
    }

    function dibujar(e) {
        if (!dibujando) return;
        e.preventDefault();
        const pos = obtenerPosicion(e, canvas);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function detenerTrazo() {
        dibujando = false;
        ctx.closePath();
    }
}

function obtenerPosicion(e, canvas) {
    const rect = canvas.getBoundingClientRect();
    let clienteX = e.clientX;
    let clienteY = e.clientY;

    if (e.touches && e.touches.length > 0) {
        clienteX = e.touches[0].clientX;
        clienteY = e.touches[0].clientY;
    }

    return {
        x: clienteX - rect.left,
        y: clienteY - rect.top
    };
}

window.limpiarCanvas = function(canvasId) {
    const canvas = document.getElementById(canvasId);
    const placeholderId = canvasId.replace('canvas', 'placeholder');
    const placeholder = document.getElementById(placeholderId);
    
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        canvas.setAttribute('data-dibujado', 'false');
    }
    
    if (placeholder) {
        placeholder.style.display = 'block';
        placeholder.innerHTML = "<i class='fa-solid fa-pen-nib'></i> Dibuje su firma aquí";
        placeholder.style.color = "#888";
    }
    
    const fileInputId = canvasId.replace('canvas', 'file');
    const fileInput = document.getElementById(fileInputId);
    if(fileInput) fileInput.value = '';
};

function obtenerImagenCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas && canvas.getAttribute('data-dibujado') === 'true') {
        return canvas.toDataURL("image/png"); // Devuelve el Base64 para Django
    }
    return "";
}

function ocultarPlaceholder(placeholderId) {
    const placeholder = document.getElementById(placeholderId);
    if (placeholder) {
        placeholder.innerHTML = "<i class='fa-solid fa-check'></i> Archivo adjuntado";
        placeholder.style.color = "#A3BD31";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const modalFirmas = document.getElementById('modal-firmas');
    const btnAbrirFirmas = document.getElementById('btn-abrir-firmas');
    const btnCancelar = document.querySelector('#modal-firmas .btn-cancelar');

    // --- 1. ABRIR MODAL Y CARGAR CANVAS ---
    if (btnAbrirFirmas && modalFirmas) {
        btnAbrirFirmas.addEventListener('click', (e) => {
            e.preventDefault();
            modalFirmas.classList.add('active'); 
            modalFirmas.style.display = 'flex'; 

            // Esperar 200ms a que la animación termine para que el canvas tenga tamaño real
            setTimeout(() => {
                iniciarCanvas('canvas-autor', 'placeholder-autor');
                iniciarCanvas('canvas-supervisor', 'placeholder-supervisor');
            }, 200); 
        });
    }

    // --- 2. CERRAR MODAL ---
    if (btnCancelar && modalFirmas) {
        btnCancelar.addEventListener('click', (e) => {
            e.preventDefault();
            modalFirmas.classList.remove('active');
            modalFirmas.style.display = 'none';
        });
    }

    // ==========================================
    // 3. AUTOCOMPLETADO MÁGICO (HOVER / FOCUS)
    // ==========================================
    if (modalFirmas) {
        const nombreUser = modalFirmas.getAttribute('data-user-nombre').trim();
        const cedulaUser = modalFirmas.getAttribute('data-user-cedula').trim();
        let rolUsado = null; // Candado de seguridad

        function intentarAutocompletar(rol) {
            if (!nombreUser && !cedulaUser) return; // Si no hay datos, no hace nada
            if (rolUsado !== null && rolUsado !== rol) return; // Bloquea si ya firmó el otro lado

            if (rol === 'autor') {
                const inpNombre = document.getElementById('input_nombre_autor');
                const inpCedula = document.getElementById('input_cedula_autor');
                if (inpNombre && inpNombre.value === "") inpNombre.value = nombreUser;
                if (inpCedula && inpCedula.value === "") inpCedula.value = cedulaUser;
            } else {
                const inpNombre = document.getElementById('input_nombre_supervisor');
                const inpCedula = document.getElementById('input_cedula_supervisor');
                if (inpNombre && inpNombre.value === "") inpNombre.value = nombreUser;
                if (inpCedula && inpCedula.value === "") inpCedula.value = cedulaUser;
            }
            rolUsado = rol; // Cierra el candado
        }

        // Sensores de Autor
        ['input_nombre_autor', 'input_cedula_autor'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('mouseover', () => intentarAutocompletar('autor'));
                el.addEventListener('focus', () => intentarAutocompletar('autor'));
            }
        });

        // Sensores de Supervisor
        ['input_nombre_supervisor', 'input_cedula_supervisor'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('mouseover', () => intentarAutocompletar('supervisor'));
                el.addEventListener('focus', () => intentarAutocompletar('supervisor'));
            }
        });
    }

    // ==========================================
    // 4. ENVÍO DE FIRMAS POR AJAX
    // ==========================================
    const formFirmas = document.getElementById('form-firmas');
    if (formFirmas) {
        formFirmas.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Extraemos el ID de la bitácora que está abierta en el cuaderno
            const idBitacoraMain = document.getElementById('id_bitacora');
            if (!idBitacoraMain || !idBitacoraMain.value) {
                alert("Debes llenar algún dato (ej: Clima) para que la bitácora se cree antes de poder firmarla.");
                return;
            }
            document.getElementById('id_bitacora_firma').value = idBitacoraMain.value;

            // Extraemos el canvas a Base64
            document.getElementById('firma_dibujada_autor').value = obtenerImagenCanvas('canvas-autor');
            document.getElementById('firma_dibujada_supervisor').value = obtenerImagenCanvas('canvas-supervisor');

            // Enviamos por Fetch API
            const formData = new FormData(formFirmas);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const urlParams = window.location.pathname.split('/');
            const idProyecto = urlParams[urlParams.indexOf('proyecto') + 1];
            
            const btnSubmit = formFirmas.querySelector('.btn-guardar');
            const textoOriginal = btnSubmit.innerHTML;
            btnSubmit.innerHTML = "Guardando firmas...";
            btnSubmit.disabled = true;

            try {
                const response = await fetch(`/bitacora/api/guardar_firmas/${idProyecto}/`, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken }
                });

                const data = await response.json();
                if (data.status === 'success') {
                    alert("¡Firmas guardadas exitosamente!");
                    window.location.reload(); // Recarga para aplicar los cambios
                } else {
                    alert("Error: " + data.message);
                }
            } catch (error) {
                console.error("Error enviando firmas:", error);
                alert("Hubo un error de conexión.");
            } finally {
                btnSubmit.innerHTML = textoOriginal;
                btnSubmit.disabled = false;
            }
        });
    }

    // --- 5. OCULTAR PLACEHOLDER AL SUBIR ARCHIVO ---
    const fileAutor = document.getElementById('file_autor');
    const fileSupervisor = document.getElementById('file_supervisor');
    
    if(fileAutor) fileAutor.addEventListener('change', () => ocultarPlaceholder('placeholder-autor'));
    if(fileSupervisor) fileSupervisor.addEventListener('change', () => ocultarPlaceholder('placeholder-supervisor'));
});

// ==========================================
// LÓGICA DE DIBUJO EN CANVAS
// ==========================================

function iniciarCanvas(canvasId, placeholderId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    
    const rect = canvas.parentElement.getBoundingClientRect();
    if (rect.width === 0) return; 
    
    canvas.width = rect.width;
    canvas.height = rect.height;

    const ctx = canvas.getContext('2d');
    const placeholder = document.getElementById(placeholderId);
    
    let dibujando = false;

    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#1a252f"; 

    canvas.addEventListener('mousedown', iniciarTrazo);
    canvas.addEventListener('mousemove', dibujar);
    canvas.addEventListener('mouseup', detenerTrazo);
    canvas.addEventListener('mouseout', detenerTrazo);

    canvas.addEventListener('touchstart', iniciarTrazo, {passive: false});
    canvas.addEventListener('touchmove', dibujar, {passive: false});
    canvas.addEventListener('touchend', detenerTrazo);

    function iniciarTrazo(e) {
        e.preventDefault(); 
        dibujando = true;
        if(placeholder) placeholder.style.display = 'none';
        canvas.setAttribute('data-dibujado', 'true');
        
        ctx.beginPath();
        const pos = obtenerPosicion(e, canvas);
        ctx.moveTo(pos.x, pos.y);
    }

    function dibujar(e) {
        if (!dibujando) return;
        e.preventDefault();
        const pos = obtenerPosicion(e, canvas);
        ctx.lineTo(pos.x, pos.y);
        ctx.stroke();
    }

    function detenerTrazo() {
        dibujando = false;
        ctx.closePath();
    }
}

function obtenerPosicion(e, canvas) {
    const rect = canvas.getBoundingClientRect();
    let clienteX = e.clientX;
    let clienteY = e.clientY;

    if (e.touches && e.touches.length > 0) {
        clienteX = e.touches[0].clientX;
        clienteY = e.touches[0].clientY;
    }

    return {
        x: clienteX - rect.left,
        y: clienteY - rect.top
    };
}

window.limpiarCanvas = function(canvasId) {
    const canvas = document.getElementById(canvasId);
    const placeholderId = canvasId.replace('canvas', 'placeholder');
    const placeholder = document.getElementById(placeholderId);
    
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        canvas.setAttribute('data-dibujado', 'false');
    }
    
    if (placeholder) {
        placeholder.style.display = 'block';
        placeholder.innerHTML = "<i class='fa-solid fa-pen-nib'></i> Dibuje su firma aquí";
        placeholder.style.color = "#888";
    }
    
    const fileInputId = canvasId.replace('canvas', 'file');
    const fileInput = document.getElementById(fileInputId);
    if(fileInput) fileInput.value = '';
};

function obtenerImagenCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (canvas && canvas.getAttribute('data-dibujado') === 'true') {
        return canvas.toDataURL("image/png"); 
    }
    return "";
}

function ocultarPlaceholder(placeholderId) {
    const placeholder = document.getElementById(placeholderId);
    if (placeholder) {
        placeholder.innerHTML = "<i class='fa-solid fa-check'></i> Archivo adjuntado";
        placeholder.style.color = "#A3BD31";
    }
}