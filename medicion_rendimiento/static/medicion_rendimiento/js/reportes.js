document.addEventListener("DOMContentLoaded", () => {
    initGraficos();
    initGraficosCuadrillas();
    initCarruselCuadrillas();
    initGraficosCostoCuadrillas();
    initGraficoDemandaPersonal();
    initGraficoDiagnosticoRendimiento();
});

document.getElementById("rango-fecha").addEventListener("change", () => {
    const modoActivo = document.getElementById("btn-mes").classList.contains("active") ? "mes" : "dia";
    
    // Solo actualizar gráfico si estamos en modo diario
    if (modoActivo === "dia") {
        cargarDemanda("dia");
    }
});



const formatoCOP = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
});

/* Inicializador general */

function initGraficos() {
    if (typeof labelsRR !== "undefined") {
        graficoRendimientoRealMensual(
            "graficoRendimientoMensual",
            labelsRR,
            dataRR,
            UNIDAD_MEDIDA,
            CUMPLIMIENTO_PROGRAMADO);
    }
}

/* Función para calcular el color de la barra según el valor y el objetivo */

function calcularColorBarra(valor, objetivo) {
    const tolerancia = 0.01;
    if (valor < objetivo - tolerancia) return "#E74C3C";
    if (Math.abs(valor - objetivo) <= tolerancia) return "#F1C40F";
    return "#A3BD31";
}

/* Grafico: Rendimiento real de la actividad (mensual) */

function graficoRendimientoRealMensual(canvasId, labels, data, unidad, objetivo) {

    const canvas = document.getElementById(canvasId)
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const colores = data.map(valor =>
        calcularColorBarra(valor, objetivo)
    );

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: `Rendimiento real (${unidad}/h)`,
                data: data,
                backgroundColor: colores,
                borderRadius: 6,
                animations: {
                    y:{
                        type: 'number', 
                        from: 1000,
                        duration: 1500, // Duración de la animación en milisegundos
                        easing: 'easeOutQuart', // Tipo de animación
                    }
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: value => `${value} ${unidad}/h`
                    }
                }
            },

            plugins: {
                legend: {
                    display: false      
                },
            
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const remdimiento = context.parsed.y;

                            return [
                                `Rendimiento real: ${remdimiento} ${unidad}/h`,
                                `Cumplimiento programado: ${objetivo} ${unidad}/h`
                            ];
                        }      
                    }
                }
            }
        }
    });
}

/* Gráficos por cuadrilla */
function initGraficosCuadrillas() {

    if (typeof GRAFICOS_CUADRILLAS === "undefined") return;
    if (!Array.isArray(GRAFICOS_CUADRILLAS)) return;

    GRAFICOS_CUADRILLAS.forEach((g, index) => {

        const canvasId = `grafico-cuadrilla-${index + 1}`;
        const canvas = document.getElementById(canvasId);

        if (!canvas) return;

        graficoCumplimientoProgramado(
            canvasId,
            g.labels,
            g.rendimiento_real,
            CUMPLIMIENTO_PROGRAMADO,
            UNIDAD_MEDIDA
        );
    });
}

function graficoCumplimientoProgramado(canvasId, labels, dataReal, objetivo, unidad) {

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Cumplimiento Programado",
                    data: labels.map(() => objetivo),
                    borderColor: "#01d32b",
                    backgroundColor: "#01d32b",
                    tension: 0,
                    borderWidth: 2,
                    pointRadius: 1,
                    pointHoverRadius: 0,
                },
                {
                    label: "Rendimiento Real",
                    data: dataReal,
                    borderColor: "#3498db",
                    backgroundColor: "#3498db",
                    pointRadius: dataReal.every(v => v === null) ? 0 : 3,
                    spanGaps: false,
                    tension: .3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: v => `${v} ${unidad}/h`
                    }
                }
            },

            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,     
                        boxHeight: 12,    
                        padding: 10,      
                            size: 11     
                    }
                },
                tooltip:{
                    callbacks: {
                        label: function(context) {
                            const valor = context.parsed.y;

                            if (valor === null) {
                                return "Sin datos";
                            }

                            const valorFormateado = valor.toFixed(2);

                            if (context.dataset.label === "Cumplimiento Programado") {
                                return `Cumplimiento Programado: ${valorFormateado} ${unidad}/h`;
                            }

                            return `Rendimiento Real: ${valorFormateado} ${unidad}/h`;
                        }
                    }
                }
            }
        }
    });
}

function initGraficosCostoCuadrillas() {

    if (!Array.isArray(GRAFICOS_COSTO_CUADRILLAS)) return;

    GRAFICOS_COSTO_CUADRILLAS.forEach((g, index) => {

        const canvasId = `grafico-costo-cuadrilla-${index + 1}`;
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        graficoCostoVsPresupuesto(
            canvasId,
            g.labels,
            g.costo_por_unidad,
            CUMPLIMIENTO_PRESUPUESTAL
        );
    });
}

function graficoCostoVsPresupuesto(canvasId, labels, dataCosto, presupuesto) {

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Cumplimiento presupuestal",
                    data: labels.map(() => presupuesto),
                    borderColor: "#E67E22",
                    backgroundColor: "#E67E22",
                    borderWidth: 2,
                    pointRadius: 1,
                    tension: 0,
                    pointHoverRadius: 0,
                },
                {
                    label: "Costo por unidad",
                    data: dataCosto,
                    borderColor: "#8E44AD",
                    backgroundColor: "#8E44AD",
                    pointRadius: dataCosto.every(v => v === null) ? 0 : 3,
                    spanGaps: false,
                    tension: .3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: v => formatoCOP.format(v)
                    }
                }
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,     
                        boxHeight: 12,    
                        padding: 10,      
                            size: 11     
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const valor = context.parsed.y;

                            if (valor === null) {
                                return "Sin datos";
                            }

                            const valorCOP = formatoCOP.format(valor);

                            if (context.dataset.label === "Cumplimiento presupuestal") {
                                return `Presupuesto: ${valorCOP}`;
                            }

                            return `Costo por unidad: ${valorCOP}`;
                        }
                    }
                }
            }
        }
    });
}

/* Carrusel de cuadrillas */
function initCarruselCuadrillas() {

    const carouseles = document.querySelectorAll('.carousel-cuadrillas');
    if (!carouseles.length) return;

    carouseles.forEach(carousel => {

        const slides = carousel.querySelectorAll('.carousel-slide');
        const btnNext = carousel.querySelector('.carousel-btn.next');
        const btnPrev = carousel.querySelector('.carousel-btn.prev');

        if (!slides.length || !btnNext || !btnPrev) return;

        let indexActual = 0;

        function mostrarSlide(index) {
            slides.forEach(s => s.classList.remove('active'));
            slides[index].classList.add('active');
        }

        btnNext.addEventListener('click', () => {
            indexActual = (indexActual + 1) % slides.length;
            mostrarSlide(indexActual);
        });

        btnPrev.addEventListener('click', () => {
            indexActual = (indexActual - 1 + slides.length) % slides.length;
            mostrarSlide(indexActual);
        });
    });
}

let graficoDemanda = null;

document.addEventListener("DOMContentLoaded", () => {
    initGraficoDemandaPersonal();
});

function initGraficoDemandaPersonal() {
    // 🔹 estado inicial
    cargarDemanda("mes");

    document.getElementById("btn-mes").addEventListener("click", () => {
        activarBoton("mes");
        cargarDemanda("mes");
    });

    document.getElementById("btn-dia").addEventListener("click", () => {
        activarBoton("dia");
        cargarDemanda("dia");
    });
}

function activarBoton(modo) {
    document.getElementById("btn-mes").classList.toggle("active", modo === "mes");
    document.getElementById("btn-dia").classList.toggle("active", modo === "dia");
}

function cargarDemanda(modo) {
    let url = `/medicion_rendimiento/api/demanda-empleados/?modo=${modo}`;

    if (modo === "dia") {
        // Solo enviar fechas en modo diario
        const fechaInicio = document.getElementById("fecha_inicio").value;
        const fechaFin = document.getElementById("fecha_fin").value;
        url += `&fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
    }

    fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" }
    })
        .then(res => {
            if (!res.ok) throw new Error("Respuesta inválida del servidor");
            return res.json();
        })
        .then(data => {
            renderGraficoDemanda(
                "grafico-demanda-personal",
                data.labels,
                data.datasets
            );
        })
        .catch(err => console.error("Error cargando demanda:", err));
}

function renderGraficoDemanda(canvasId, labels, datasetsRaw) {
    const ctx = document.getElementById(canvasId).getContext("2d");

    if (graficoDemanda) {
        graficoDemanda.destroy();
    }

    const colores = [
        "#3498DB", "#9B59B6", "#E67E22",
        "#2ECC71", "#E74C3C", "#F1C40F"
    ];

    const datasets = datasetsRaw.map((d, i) => ({
        label: d.label,
        data: d.data,
        borderColor: colores[i % colores.length],
        backgroundColor: colores[i % colores.length],
        borderWidth: 2,
        tension: 0.3,
        fill: false,
        pointRadius: 3,
        pointHoverRadius: 0
    }));

    graficoDemanda = new Chart(ctx, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        boxWidth: 12,     
                        boxHeight: 12,    
                        padding: 10,      
                            size: 11     
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx =>
                            `${ctx.dataset.label}: ${ctx.parsed.y} personas`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Cantidad de personas"
                    },
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

function calcularPercentil(arr, p) {
    if (!arr.length) return 0;

    const ordenados = [...arr].sort((a, b) => a - b);
    const index = (p / 100) * (ordenados.length - 1);
    const lower = Math.floor(index);
    const upper = Math.ceil(index);

    if (lower === upper) return ordenados[lower];

    return ordenados[lower] + 
           (ordenados[upper] - ordenados[lower]) * (index - lower);
}

function initGraficoDiagnosticoRendimiento() {
    if (typeof DIAGNOSTICO_RENDIMIENTO === "undefined") return;

    renderGraficoDiagnosticoRendimiento(
        "graficoDiagnosticoRendimiento",
        "valorDiagnostico",
        DIAGNOSTICO_RENDIMIENTO
    );
}

let graficoDiagnostico = null;

function renderGraficoDiagnosticoRendimiento(canvasId, valorId, data) {

    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (graficoDiagnostico) {
        graficoDiagnostico.destroy();
    }

    const valores = data.valores;
    if (valores.length < 3) return;

    const promedio = data.promedio;

    // 🔹 percentiles
    const p20 = calcularPercentil(valores, 20);
    const p80 = calcularPercentil(valores, 80);

    const min = Math.min(...valores);
    const max = Math.max(...valores);
    const margen = (max - min) * 0.1;

    const minVisual = Math.max(0, min - margen);
    const maxVisual = max + margen;

    // 🔹 segmentos iguales (visual)
    const segmentos = [
        p20 - minVisual,
        p80 - p20,
        maxVisual - p80
    ];

    graficoDiagnostico = new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [{
                data: segmentos,
                backgroundColor: [
                    "#E74C3C", // crítico
                    "#F1C40F", // aceptable
                    "#2ECC71"  // excelente
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "75%",
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });

    // 🔹 valor central
    const valorCentral = document.getElementById(valorId);
    if (valorCentral) {
        valorCentral.innerHTML = `
            <strong>${promedio.toFixed(1)}%</strong>
            <br>
            <small>${
                promedio < p20 ? "CRÍTICO" :
                promedio < p80 ? "ACEPTABLE" :
                "EXCELENTE"
            }</small>
        `;
    }
}
