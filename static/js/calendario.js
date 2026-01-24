document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("rango-fecha");
    const form = document.getElementById("filtros-form");

    const fechaInicioInput = document.getElementById("fecha_inicio");
    const fechaFinInput = document.getElementById("fecha_fin");

    const fechaInicio = input.dataset.inicio;
    const fechaFin = input.dataset.fin;

    flatpickr(input, {
        mode: "range",
        dateFormat: "Y-m-d",
        altInput: true,
        altFormat: "d/m/Y",
        locale: flatpickr.l10ns.es,
        allowInput: false,
        defaultDate: fechaInicio && fechaFin ? [fechaInicio, fechaFin] : null,

        onClose: function (selectedDates) {
            if (selectedDates.length === 2) {

                const inicio = selectedDates[0].toISOString().split("T")[0];
                const fin = selectedDates[1].toISOString().split("T")[0];

                fechaInicioInput.value = inicio;
                fechaFinInput.value = fin;

                form.submit();
            }
        }
    });
});