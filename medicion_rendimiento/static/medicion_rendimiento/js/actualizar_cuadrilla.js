function inicializarActualizarCuadrilla(contenedor) {
    if (!contenedor || !document.body.contains(contenedor)) {
        console.warn("Modal no disponible o ya cerrado");
        return;
    }

    /* ===============================
       VALIDACIÓN ACTIVIDAD FINALIZADA
    ================================ */
    const checkboxSeleccionado = document.querySelector(
        'input[name="elemento"]:checked'
    );

    if (checkboxSeleccionado?.dataset.finalizada === "1") {
        alert("⚠️ Esta actividad ya fue finalizada y no puede ser actualizada.");
        contenedor.innerHTML = "";
        contenedor.style.display = "none";
        return;
    }

    console.log("📌 Inicializando actualización de cuadrilla");

    /* ===============================
       ELEMENTOS
    ================================ */
    const btnContinuar = contenedor.querySelector("#btn-continuar");
    const btnAceptar  = contenedor.querySelector("#btn-aceptar"); // queda oculto
    const paso2       = contenedor.querySelector("#paso-2");
    const tituloPersona = contenedor.querySelector("#titulo-persona");

    const horaEntradaWrapper = contenedor.querySelector("#grupo-hora-entrada");
    const horaSalidaWrapper  = contenedor.querySelector("#grupo-hora-salida");
    const inputEntrada = contenedor.querySelector("#input-hora-entrada");
    const inputSalida  = contenedor.querySelector("#input-hora-salida");

    const formActualizar = contenedor.querySelector("#form-actualizar-cuadrilla");
    const checkSalieron  = contenedor.querySelectorAll("input[name='empleados_salieron']");
    const checkEntraron  = contenedor.querySelectorAll("input[name='empleados_entraron']");

    /* ===============================
       ESTADO
    ================================ */
    let personasSeleccionadas = [];
    let indexActual = 0;
    let enviado = false;

    /* ===============================
       FUNCIONES AUXILIARES
    ================================ */
    function obtenerNombrePorCedula(cedula) {
        const input = contenedor.querySelector(`input[value="${cedula}"]`);
        return input?.parentElement?.innerText.trim() || "Empleado";
    }

    function ocultarGruposComidas() {
        contenedor.querySelectorAll(".grupo-comidas")
            .forEach(div => div.style.display = "none");
    }

    function actualizarTextoBoton() {
        const esUltimo = indexActual === personasSeleccionadas.length - 1;
        btnContinuar.textContent = esUltimo ? "Guardar" : "Continuar";
    }

    function mostrarPersonaActual() {
        const persona = personasSeleccionadas[indexActual];
        if (!persona) return;

        tituloPersona.textContent =
            `${obtenerNombrePorCedula(persona.cedula)} (${persona.tipo})`;

        inputEntrada.value = "";
        inputSalida.value = "";

        if (persona.tipo === "salio") {
            horaEntradaWrapper.style.display = "none";
            horaSalidaWrapper.style.display = "block";
            inputSalida.value = persona.hora || "";
        } else {
            horaSalidaWrapper.style.display = "none";
            horaEntradaWrapper.style.display = "block";
            inputEntrada.value = persona.hora || "";
        }

        ocultarGruposComidas();

        const grupoActual = contenedor.querySelector(
            `.grupo-comidas[data-cedula="${persona.cedula}"]`
        );
        if (grupoActual) grupoActual.style.display = "block";

        actualizarTextoBoton();
    }

    function guardarHoraPersonaActual() {
        const persona = personasSeleccionadas[indexActual];
        if (!persona) return false;

        const hora = persona.tipo === "salio"
            ? inputSalida.value.trim()
            : inputEntrada.value.trim();

        if (!hora) {
            alert(`Debes ingresar la hora de ${persona.tipo === "salio" ? "salida" : "entrada"}.`);
            return false;
        }

        persona.hora = hora;
        return true;
    }

    function enviarFormulario() {
        if (enviado) return;
        enviado = true;

        const inputHidden = document.createElement("input");
        inputHidden.type = "hidden";
        inputHidden.name = "registro_cambios";
        inputHidden.value = JSON.stringify(personasSeleccionadas);

        formActualizar.appendChild(inputHidden);

        console.log("➡️ Enviando formulario:", personasSeleccionadas);
        formActualizar.submit();
    }

    /* ===============================
       CLICK CONTINUAR / GUARDAR
    ================================ */
    btnContinuar?.addEventListener("click", () => {

        // PASO 2 → recorrer personas
        if (paso2.style.display === "block") {
            if (!guardarHoraPersonaActual()) return;

            const esUltimo = indexActual === personasSeleccionadas.length - 1;

            if (esUltimo) {
                enviarFormulario();
                return;
            }

            indexActual++;
            mostrarPersonaActual();
            return;
        }

        // PRIMER CLICK → seleccionar personas
        const salieron = [...checkSalieron].filter(c => c.checked).map(c => c.value);
        const entraron = [...checkEntraron].filter(c => c.checked).map(c => c.value);

        personasSeleccionadas = [
            ...salieron.map(c => ({ cedula: c, tipo: "salio" })),
            ...entraron.map(c => ({ cedula: c, tipo: "entro" }))
        ];

        if (personasSeleccionadas.length === 0) {
            alert("Debes seleccionar al menos una persona.");
            return;
        }

        contenedor.querySelectorAll(".funcionalidades-box")
            .forEach(box => box.style.display = "none");

        paso2.style.display = "block";
        btnAceptar.style.display = "none";

        indexActual = 0;
        mostrarPersonaActual();
    });
}
