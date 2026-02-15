document.querySelectorAll('input[type="file"]').forEach(fileInput => {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        const submitBtn = e.target.closest('form').querySelector('button[type="submit"]');
        const textSpan = e.target.parentElement.querySelector('.fileText');
        
        // Si no hay archivo o no es imagen, nos aseguramos de habilitar el botón y salir
        if (!file || !file.type.startsWith('image/')) {
            if(submitBtn) submitBtn.disabled = false;
            return;
        }

        // Bloqueamos el envío mientras procesamos
        if(submitBtn) submitBtn.disabled = true;
        const originalText = textSpan.innerText;
        textSpan.innerText = "⏳ Optimizando imagen...";

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onerror = () => { if(submitBtn) submitBtn.disabled = false; };
        
        reader.onload = function(event) {
            const img = new Image();
            img.src = event.target.result;
            img.onload = function() {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;
                const MAX_WIDTH = 1200; 

                if (width > MAX_WIDTH) {
                    height *= MAX_WIDTH / width;
                    width = MAX_WIDTH;
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    const compressedFile = new File([blob], file.name, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });

                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(compressedFile);
                    e.target.files = dataTransfer.files;
                    
                    textSpan.innerText = "Foto lista";
                    textSpan.style.color = "#28a745";

                    // ¡Liberamos el botón!
                    if(submitBtn) submitBtn.disabled = false;
                }, 'image/jpeg', 0.6); 
            };
        };
    });
});