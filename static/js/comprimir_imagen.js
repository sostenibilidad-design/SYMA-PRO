document.querySelectorAll('input[type="file"]').forEach(fileInput => {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const form = e.target.closest('form');
        const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
        const textSpan = e.target.parentElement.querySelector('.fileText');
        
        // Si no hay archivo o no es imagen, habilitamos y salimos
        if (!file || !file.type.startsWith('image/')) {
            if(submitBtn) submitBtn.disabled = false;
            return;
        }

        // Bloqueamos el botón de envío
        if(submitBtn) submitBtn.disabled = true;
        if(textSpan) {
            textSpan.innerText = "⏳ Optimizando imagen...";
            textSpan.style.color = "#ffc107"; // Color de espera
        }

        // Creamos la imagen en memoria
        const img = new Image();
        
        img.onload = function() {
            // 🔴 TRUCO DE MAGIA: Liberamos la RAM inmediatamente después de cargarla
            URL.revokeObjectURL(img.src);

            const canvas = document.createElement('canvas');
            let width = img.width;
            let height = img.height;
            const MAX_WIDTH = 1200; 

            // Calculamos la nueva proporción
            if (width > MAX_WIDTH) {
                const ratio = MAX_WIDTH / width;
                width = MAX_WIDTH;
                height = Math.round(height * ratio);
            }

            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            // Convertimos el canvas a un archivo pequeño (60% calidad)
            canvas.toBlob((blob) => {
                if (!blob) {
                    if(submitBtn) submitBtn.disabled = false;
                    if(textSpan) textSpan.innerText = "❌ Error al comprimir";
                    return;
                }

                const compressedFile = new File([blob], file.name, {
                    type: 'image/jpeg',
                    lastModified: Date.now()
                });

                // Engañamos al input para que tome nuestro archivo liviano
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(compressedFile);
                e.target.files = dataTransfer.files;
                
                if(textSpan) {
                    textSpan.innerText = "✅ Foto lista";
                    textSpan.style.color = "#28a745"; // Verde de éxito
                }

                // ¡Liberamos el botón!
                if(submitBtn) submitBtn.disabled = false;

                if (typeof window.cerrarOpcionesFoto === "function") {
                    window.cerrarOpcionesFoto();
                } else {
                    const modalOpciones = document.getElementById('modal-opciones-foto');
                    if (modalOpciones) modalOpciones.classList.remove('active');
                }
            }, 'image/jpeg', 0.6);
        };

        img.onerror = function() {
            if(submitBtn) submitBtn.disabled = false;
            if(textSpan) textSpan.innerText = "❌ Error al leer imagen";
            if (typeof window.cerrarOpcionesFoto === "function") {
                    window.cerrarOpcionesFoto();
                } else {
                    const modalOpciones = document.getElementById('modal-opciones-foto');
                    if (modalOpciones) modalOpciones.classList.remove('active');
                }
        };

        // 🚀 ESTA ES LA CLAVE: Usamos un puntero ligero en lugar de leer todo el texto
        img.src = URL.createObjectURL(file);
    });
});