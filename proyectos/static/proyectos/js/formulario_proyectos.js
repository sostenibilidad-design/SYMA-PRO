document.addEventListener("DOMContentLoaded", () => {
    const inputFoto = document.getElementById("rp-input-foto");
    const previewIcon = document.getElementById("rp-preview-icon");
    const previewImage = document.getElementById("rp-preview-image");

    if (inputFoto) {
        inputFoto.addEventListener("change", function(event) {
            const archivo = event.target.files[0];
            
            if (archivo && archivo.type.startsWith('image/')) {
                const urlImagen = URL.createObjectURL(archivo);
                
                previewIcon.style.display = "none";
                previewImage.src = urlImagen;
                previewImage.style.display = "block";
                
                const textoBoton = this.parentElement.querySelector("span");
                if (textoBoton) textoBoton.innerText = "Imagen seleccionada";
            }
        });
    }

    // --- LÓGICA DEL CUSTOM SELECT ---
    const customSelect = document.querySelector('.syma-custom-select');
    if (customSelect) {
        const selectedBox = customSelect.querySelector('.select-selected');
        const optionsList = customSelect.querySelector('.select-items');
        const hiddenInput = customSelect.querySelector('#input-estado');
        const selectedText = customSelect.querySelector('.selected-text');
        const options = optionsList.querySelectorAll('div');

        // 1. Abrir/Cerrar la lista al hacer clic
        selectedBox.addEventListener('click', function(e) {
            e.stopPropagation();
            customSelect.classList.toggle('active');
        });

        // 2. Seleccionar una opción
        options.forEach(option => {
            option.addEventListener('click', function() {
                // Actualizar el texto visual
                selectedText.innerText = this.innerText;
                selectedText.style.color = '#666'; // Cambia de gris claro (placeholder) a texto normal
                
                // Actualizar el input oculto para Django
                hiddenInput.value = this.getAttribute('data-value');
                
                // Cerrar la lista
                customSelect.classList.remove('active');
            });
        });

        // 3. Cerrar si el usuario hace clic en cualquier otra parte de la pantalla
        document.addEventListener('click', function(e) {
            if (!customSelect.contains(e.target)) {
                customSelect.classList.remove('active');
            }
        });
    }
});

