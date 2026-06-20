document.addEventListener("DOMContentLoaded", function() {
    let inputUrl = document.getElementById("url-api-actividades");
    if (!inputUrl) return; 
    
    let apiUrl = inputUrl.value;

    setTimeout(function() {
        fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            let contenedorActividades = document.querySelector(".lista-actividades");
            let textoSeleccionado = document.getElementById("texto-actividad-seleccionada");
            
            if (contenedorActividades) {
                // Verificamos si el usuario ya había elegido algo antes de la actualización
                let opcionElegida = document.querySelector('input[name="actividad"]:checked');
                let valorElegido = opcionElegida ? opcionElegida.value : null;

                // Vaciamos la lista vieja
                contenedorActividades.innerHTML = ""; 
                let encontrado = false;

                // Llenamos con el nuevo diseño
                data.actividades.forEach(act => {
                    // Mantenemos la selección si ya había elegido una
                    let isChecked = (valorElegido === act.valor) ? "checked" : "";
                    if (isChecked) encontrado = true;

                    let div = document.createElement("div");
                    div.className = "area-item actividad-item";
                    div.innerHTML = `
                        <label class="area-label">
                            <input type="radio" name="actividad" class="area-checkbox radio-actividad" value="${act.valor}" ${isChecked} required>
                            <strong>${act.texto}</strong>
                        </label>
                    `;
                    contenedorActividades.appendChild(div);
                });
                
                // Si la actividad que había elegido la borraron del Drive, limpiamos el texto
                if (valorElegido && !encontrado && textoSeleccionado) {
                    textoSeleccionado.textContent = "Seleccione una actividad";
                }
                
                console.log("Misión Ninja: Actividades (Única Selección) actualizadas silenciosamente.");
            }
        })
        .catch(error => console.log("Error en actualización ninja:", error));
        
    }, 5000); 
});