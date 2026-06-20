let inputFotoDestino = "";

window.abrirOpcionesFoto = function(idInput) {
    inputFotoDestino = idInput; // Guardamos en memoria cuál input pidió la foto
    document.getElementById('modal-opciones-foto').classList.add('active');
};

window.cerrarOpcionesFoto = function() {
    document.getElementById('modal-opciones-foto').classList.remove('active');
};

window.elegirOrigenFoto = function(origen) {
    let inputEl = document.getElementById(inputFotoDestino);
    if (!inputEl) return;

    if (origen === 'camara') {
        // Obliga al celular a abrir la cámara trasera
        inputEl.setAttribute('capture', 'environment');
    } else {
        // Abre los archivos/galería normal
        inputEl.removeAttribute('capture');
    }

    // 🔥 ELIMINAMOS el cerrarOpcionesFoto() de aquí para que espere
    
    setTimeout(() => {
        inputEl.click();
    }, 100);
};