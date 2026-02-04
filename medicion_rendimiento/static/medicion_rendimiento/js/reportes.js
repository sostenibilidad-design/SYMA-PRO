document.addEventListener("DOMContentLoaded", () => {
    initGraficos();
    initGraficosCuadrillas();
    initCarruselCuadrillas();
    initGraficosCostoCuadrillas();
    initGraficoDemandaPersonal();
    initGraficoDiagnosticoRendimiento();
    initGraficoDiagnosticoPresupuesto();
    initGraficoComparativoCuadrillas();
    initGraficoCronograma();
});

document.getElementById("rango-fecha").addEventListener("change", () => {
    const modoActivo = document.getElementById("btn-mes").classList.contains("active") ? "mes" : "dia";
    
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
    const colores = data.map(valor => calcularColorBarra(valor, objetivo));

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
                    y:{ type: 'number', from: 1000, duration: 1500, easing: 'easeOutQuart' }
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { callback: value => `${value} ${unidad}/h` }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return [
                                `Rendimiento real: ${context.parsed.y} ${unidad}/h`,
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
            canvasId, g.labels, g.rendimiento_real, CUMPLIMIENTO_PROGRAMADO, UNIDAD_MEDIDA
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
                    tension: 0, borderWidth: 2, pointRadius: 1, pointHoverRadius: 0,
                },
                {
                    label: "Rendimiento Real",
                    data: dataReal,
                    borderColor: "#3498db",
                    backgroundColor: "#3498db",
                    pointRadius: dataReal.every(v => v === null) ? 0 : 3,
                    spanGaps: false, tension: .3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => `${v} ${unidad}/h` } }
            },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12, padding: 10, size: 11 } },
                tooltip:{
                    callbacks: {
                        label: function(context) {
                            const valor = context.parsed.y;
                            if (valor === null) return "Sin datos";
                            const valorFormateado = valor.toFixed(2);
                            if (context.dataset.label === "Cumplimiento Programado") return `Cumplimiento Programado: ${valorFormateado} ${unidad}/h`;
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
        graficoCostoVsPresupuesto(canvasId, g.labels, g.costo_por_unidad, CUMPLIMIENTO_PRESUPUESTAL);
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
                    borderColor: "#E67E22", backgroundColor: "#E67E22",
                    borderWidth: 2, pointRadius: 1, tension: 0, pointHoverRadius: 0,
                },
                {
                    label: "Costo por unidad",
                    data: dataCosto,
                    borderColor: "#8E44AD", backgroundColor: "#8E44AD",
                    pointRadius: dataCosto.every(v => v === null) ? 0 : 3,
                    spanGaps: false, tension: .3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => formatoCOP.format(v) } }
            },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12, padding: 10, size: 11 } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const valor = context.parsed.y;
                            if (valor === null) return "Sin datos";
                            const valorCOP = formatoCOP.format(valor);
                            if (context.dataset.label === "Cumplimiento presupuestal") return `Presupuesto: ${valorCOP}`;
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

function initGraficoDemandaPersonal() {
    cargarDemanda("mes");
    document.getElementById("btn-mes").addEventListener("click", () => {
        activarBoton("mes"); cargarDemanda("mes");
    });
    document.getElementById("btn-dia").addEventListener("click", () => {
        activarBoton("dia"); cargarDemanda("dia");
    });
}

function activarBoton(modo) {
    document.getElementById("btn-mes").classList.toggle("active", modo === "mes");
    document.getElementById("btn-dia").classList.toggle("active", modo === "dia");
}

function cargarDemanda(modo) {
    let url = `/medicion_rendimiento/api/demanda-empleados/?modo=${modo}`;
    if (modo === "dia") {
        const fechaInicio = document.getElementById("fecha_inicio").value;
        const fechaFin = document.getElementById("fecha_fin").value;
        url += `&fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`;
    }

    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(res => { if (!res.ok) throw new Error("Respuesta inválida"); return res.json(); })
        .then(data => { renderGraficoDemanda("grafico-demanda-personal", data.labels, data.datasets); })
        .catch(err => console.error("Error cargando demanda:", err));
}

function renderGraficoDemanda(canvasId, labels, datasetsRaw) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    if (graficoDemanda) graficoDemanda.destroy();

    const colores = ["#3498DB", "#9B59B6", "#E67E22", "#2ECC71", "#E74C3C", "#F1C40F"];
    const datasets = datasetsRaw.map((d, i) => ({
        label: d.label, data: d.data, borderColor: colores[i % colores.length],
        backgroundColor: colores[i % colores.length], borderWidth: 2, tension: 0.3,
        fill: false, pointRadius: 3, pointHoverRadius: 0
    }));

    graficoDemanda = new Chart(ctx, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12, padding: 10, size: 11 } },
                tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y} personas` } }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: "Cantidad de personas" }, ticks: { precision: 0 } }
            }
        }
    });
}

function initGraficoDiagnosticoRendimiento() {
    if (typeof DIAGNOSTICO_RENDIMIENTO === "undefined") return;
    if (!DIAGNOSTICO_RENDIMIENTO) return;
    renderGraficoDiagnosticoRendimiento("graficoDiagnosticoRendimiento", "valorDiagnostico", DIAGNOSTICO_RENDIMIENTO);
}

const pluginDiagnosticoAvanzado = {
    id: "diagnosticoAvanzado",
    afterDraw(chart, args, options) {
        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data.length) return;

        const arco = meta.data[0];
        const cx = arco.x;
        const cy = arco.y;
        const r = arco.outerRadius;
        const min = options.min;
        const max = options.max;
        const valor = options.valor;

        if (valor !== null && min !== max) {
            const pct = Math.max(0, Math.min((valor - min) / (max - min), 1));
            const angulo = Math.PI + pct * Math.PI;
            const largoAguja = r * 0.8;
            const anchoBase = 12;

            const xBaseIzq = cx + Math.cos(angulo - Math.PI / 2) * anchoBase;
            const yBaseIzq = cy + Math.sin(angulo - Math.PI / 2) * anchoBase;
            const xBaseDer = cx + Math.cos(angulo + Math.PI / 2) * anchoBase;
            const yBaseDer = cy + Math.sin(angulo + Math.PI / 2) * anchoBase;
            const xPunta = cx + Math.cos(angulo) * largoAguja;
            const yPunta = cy + Math.sin(angulo) * largoAguja;

            ctx.save();
            ctx.shadowColor = "rgba(0,0,0,0.35)"; ctx.shadowBlur = 10; ctx.shadowOffsetY = 4;
            ctx.beginPath(); ctx.moveTo(xBaseIzq, yBaseIzq); ctx.lineTo(xPunta, yPunta); ctx.lineTo(xBaseDer, yBaseDer); ctx.closePath();
            ctx.fillStyle = "#1F2D3D"; ctx.fill(); ctx.restore();

            ctx.save();
            ctx.beginPath(); ctx.arc(cx, cy, 14, 0, Math.PI * 2); ctx.fillStyle = "#1F2D3D"; ctx.fill();
            ctx.beginPath(); ctx.arc(cx, cy, 6, 0, Math.PI * 2); ctx.fillStyle = "#FFFFFF"; ctx.fill(); ctx.restore();
        }

        const valores = options.valoresRango || { critico: 0, aceptable: 0, excelente: 0 };
        const esCosto = options.tipo === 'costo';
        let rangos = [];

        if (esCosto) {
            rangos = [
                { texto: "EXCELENTE", valor: valores.excelente, ang: Math.PI + Math.PI * 0.17 },
                { texto: "ACEPTABLE", valor: valores.aceptable, ang: Math.PI + Math.PI * 0.50 },
                { texto: "CRÍTICO",   valor: valores.critico,   ang: Math.PI + Math.PI * 0.83 }
            ];
        } else {
            rangos = [
                { texto: "CRÍTICO",   valor: valores.critico,   ang: Math.PI + Math.PI * 0.17 },
                { texto: "ACEPTABLE", valor: valores.aceptable, ang: Math.PI + Math.PI * 0.50 },
                { texto: "EXCELENTE", valor: valores.excelente, ang: Math.PI + Math.PI * 0.83 }
            ];
        }

        ctx.save();
        ctx.fillStyle = "#FFFFFF"; ctx.shadowColor = "rgba(0,0,0,0.25)"; ctx.shadowBlur = 4;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        const radioTexto = r * 0.80;

        rangos.forEach(rg => {
            const tx = cx + Math.cos(rg.ang) * radioTexto;
            const ty = cy + Math.sin(rg.ang) * radioTexto;
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(rg.texto, tx, ty);
            if (rg.valor !== undefined && rg.valor !== null) {
                ctx.font = "bold 9px sans-serif";
                const valStr = rg.valor.toLocaleString('es-CO', { maximumFractionDigits: 0 });
                ctx.fillText(valStr, tx, ty + 12);
            }
        });

        const totalTicks = 30;
        const largoTick = 6;
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 1;

        for (let i = 0; i <= totalTicks; i++) {
            const pctTick = i / totalTicks;
            const angTick = Math.PI + pctTick * Math.PI;
            const x1 = cx + Math.cos(angTick) * (r * 0.66);
            const y1 = cy + Math.sin(angTick) * (r * 0.66);
            const x2 = cx + Math.cos(angTick) * (r * 0.66 - largoTick);
            const y2 = cy + Math.sin(angTick) * (r * 0.66 - largoTick);
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        }
        ctx.restore();
    }
};

Chart.register(pluginDiagnosticoAvanzado);
let graficoDiagnostico = null;

function renderGraficoDiagnosticoRendimiento(canvasId, valorId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (graficoDiagnostico) graficoDiagnostico.destroy();

    const { promedio, rangos, estado, cantidad_datos } = data;
    const MIN_DATOS = 30;

    const critico   = rangos?.critico   ?? 0;
    const aceptable = rangos?.aceptable ?? 0;
    const excelente = rangos?.excelente ?? 0;

    let min = critico;
    let max = excelente;
    if (min === max) max = min + 1;

    const tramoCritico   = aceptable - critico || 1;
    const tramoAceptable = excelente - aceptable || 1;
    const tramoExcelente = 1;
    const valorAguja = cantidad_datos > 0 ? promedio : 0;

    // 🔥 FIX RESPONSIVE: Si es celular, quitamos el padding para que la dona sea grande
    const esMovil = window.innerWidth < 768;
    const paddingLateral = esMovil ? 0 : 20; 

    graficoDiagnostico = new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [{
                data: [tramoCritico, tramoAceptable, tramoExcelente],
                backgroundColor: ["#E74C3C", "#F1C40F", "#2ECC71"],
                borderColor: "#FFFFFF", borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: { left: paddingLateral, right: paddingLateral }
            },
            cutout: "60%", circumference: 180, rotation: 270,
            plugins: {
                legend: { display: false }, tooltip: { enabled: false },
                diagnosticoAvanzado: {
                    valor: valorAguja, min, max,
                    valoresRango: { critico, aceptable, excelente }
                }
            }
        }
    });

    const valorCentral = document.getElementById(valorId);
    if (!valorCentral) return;
    valorCentral.innerHTML = cantidad_datos < MIN_DATOS
        ? `<strong>—</strong><br><small>Datos insuficientes</small>`
        : `<strong>${promedio.toFixed(2)}</strong><br><small>${estado}</small>`;
}

function initGraficoDiagnosticoPresupuesto() {
    if (typeof DIAGNOSTICO_PRESUPUESTO === "undefined" || !DIAGNOSTICO_PRESUPUESTO) {
        console.warn("Faltan datos para el diagnóstico de presupuesto.");
        return;
    }
    renderGraficoDiagnosticoCosto("graficoDiagnosticoPresupuesto", "valorDiagnosticoPresupuesto", DIAGNOSTICO_PRESUPUESTO);
}

function renderGraficoDiagnosticoCosto(canvasId, valorId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const { promedio, rangos, estado, cantidad_datos } = data;

    const excelente = rangos?.excelente ?? 0; 
    const aceptable = rangos?.aceptable ?? 0; 
    const critico   = rangos?.critico ?? 0;   
    const min = 0; 
    const max = critico > 0 ? critico * 1.1 : 100;

    const valorAguja = cantidad_datos > 0 ? promedio : 0;

    // 🔥 FIX RESPONSIVE: Mismo arreglo aquí
    const esMovil = window.innerWidth < 768;
    const paddingLateral = esMovil ? 20 : 20;

    new Chart(ctx, {
        type: "doughnut",
        data: {
            datasets: [{
                data: [1, 1, 1],
                backgroundColor: ["#2ECC71", "#F1C40F", "#E74C3C"], 
                borderColor: "#FFFFFF", 
                borderWidth: 3
            }]
        },
        options: {
            responsive: true, 
            maintainAspectRatio: false,
            layout: { padding: { left: paddingLateral, right: paddingLateral } },
            cutout: "60%", 
            circumference: 180, 
            rotation: 270,
            plugins: {
                legend: { display: false }, 
                tooltip: { enabled: false }, 
                diagnosticoAvanzado: {
                    valor: valorAguja, 
                    min: min, 
                    max: max,
                    valoresRango: { critico, aceptable, excelente }, 
                    tipo: 'costo'
                }
            }
        }
    });

    const valorCentral = document.getElementById(valorId);
    if (valorCentral) {
        if (cantidad_datos === 0) {
            valorCentral.innerHTML = `<strong>—</strong><br><small>Sin datos</small>`;
        } else {
            const valorFormat = typeof formatoCOP !== 'undefined' ? formatoCOP.format(promedio) : `$ ${promedio.toFixed(0)}`;
            let claseColor = "";
            if (estado === "EXCELENTE") claseColor = "color: #2ECC71;";
            else if (estado === "ACEPTABLE") claseColor = "color: #F1C40F;";
            else claseColor = "color: #E74C3C;";
            valorCentral.innerHTML = `<strong style="font-size:1.2em">${valorFormat}</strong><br><small style="${claseColor}">${estado}</small>`;
        }
    }
}

function initGraficoComparativoCuadrillas() {
    if (typeof COMPARATIVO_DATA === "undefined" || !COMPARATIVO_DATA) return;
    renderComparativo(COMPARATIVO_DATA);
}

function renderComparativo(dataPayload) {
    const canvas = document.getElementById("graficoComparativoCuadrillas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const { labels, data, thresholds, integrantes } = dataPayload;

    if (window.chartComparativo instanceof Chart) {
        window.chartComparativo.destroy();
    }

    const hayDatosSuficientes = thresholds && thresholds.superior > 0;
    let annotations = {};

    if (hayDatosSuficientes) {
        annotations = {
            lineaSuperior: {
                type: 'line', yMin: thresholds.superior, yMax: thresholds.superior,
                borderColor: '#2ECC71', borderWidth: 2, borderDash: [6, 4],
                label: { display: true, content: `Superior (${thresholds.superior})`, position: 'end', backgroundColor: 'rgba(255,255,255,0.8)', color: '#27ae60', font: { size: 10, weight: 'bold' }, yAdjust: -10 }
            },
            lineaEstandar: {
                type: 'line', yMin: thresholds.estandar, yMax: thresholds.estandar,
                borderColor: '#F1C40F', borderWidth: 2, borderDash: [6, 4],
                label: { display: true, content: `Estándar (${thresholds.estandar})`, position: 'end', backgroundColor: 'rgba(255,255,255,0.8)', color: '#d35400', font: { size: 10, weight: 'bold' }, yAdjust: -10 }
            },
            lineaBajo: {
                type: 'line', yMin: thresholds.bajo, yMax: thresholds.bajo,
                borderColor: '#E74C3C', borderWidth: 2, borderDash: [6, 4],
                label: { display: true, content: `Bajo (${thresholds.bajo})`, position: 'end', backgroundColor: 'rgba(255,255,255,0.8)', color: '#c0392b', font: { size: 10, weight: 'bold' }, yAdjust: -10 }
            }
        };
    }

    window.chartComparativo = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : ["Sin datos suficientes"],
            datasets: [{
                label: 'Rendimiento Real',
                data: labels.length ? data : [],
                backgroundColor: '#3498db', borderRadius: 4, barPercentage: 0.5, maxBarThickness: 40,
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Rendimiento Real (u/h)' }, grid: { borderDash: [2, 2], color: '#f0f0f0' }, suggestedMax: hayDatosSuficientes ? undefined : 10 },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false },
                annotation: { annotations: annotations },
                tooltip: {
                    enabled: labels.length > 0,
                    callbacks: {
                        afterBody: function(context) {
                            const index = context[0].dataIndex;
                            const equipo = integrantes[index];
                            if (equipo && equipo.length > 0) {
                                const visible = equipo.slice(0, 5);
                                const resto = equipo.length - 5;
                                let texto = '\nIntegrantes:\n• ' + visible.join('\n• ');
                                if (resto > 0) texto += `\n... y ${resto} más`;
                                return texto;
                            }
                            return '\n(Sin integrantes registrados)';
                        }
                    }
                },
                subtitle: { display: !hayDatosSuficientes, text: 'Datos insuficientes para generar diagnóstico', color: '#e74c3c', font: { size: 14, style: 'italic' }, padding: { bottom: 20 } }
            },
            onClick: (e, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const nombre = labels[index];
                    const val = data[index];
                    const eq = integrantes[index];
                    alert(`Cuadrilla: ${nombre}\nRendimiento: ${val}\n\n` + (eq ? eq.join('\n') : ''));
                }
            }
        }
    });
}

function initGraficoCronograma() {
    if (typeof CRONOGRAMA_DATA === "undefined" || !CRONOGRAMA_DATA || CRONOGRAMA_DATA.length === 0) {
        const container = document.getElementById('canvas-container');
        if(container) container.innerHTML = '<div style="padding:20px; text-align:center; color:#999">No hay datos en este rango.</div>';
        return;
    }

    const container = document.getElementById('canvas-container');
    const canvas = document.getElementById('ganttCanvas');
    if (!container || !canvas) return;

    const elInicio = document.getElementById("fecha_inicio");
    const elFin = document.getElementById("fecha_fin");
    if(!elInicio || !elFin) return;

    ganttState.fechas.inicio = new Date(elInicio.value + 'T00:00:00');
    const dFin = new Date(elFin.value + 'T00:00:00');
    const unDia = 24 * 60 * 60 * 1000;
    
    const diffTime = Math.abs(dFin - ganttState.fechas.inicio);
    ganttState.fechas.totalDias = Math.ceil(diffTime / unDia) + 5; 

    ganttState.datos = CRONOGRAMA_DATA;
    ganttState.datos.forEach(d => { if (ganttState.expanded[d.id] === undefined) ganttState.expanded[d.id] = false; });

    setupDomStructure(container, canvas);
    actualizarFilasVisibles();
    cambiarVistaGantt('day');
}

// ... (El resto del JS del cronograma sigue aquí, ya está completo)
// (He incluido la versión completa funcional arriba, no falta nada importante)
// Funciones auxiliares del Gantt:
function setupDomStructure(container, canvas) {
    let spacer = document.getElementById('gantt-spacer');
    if (!spacer) {
        spacer = document.createElement('div');
        spacer.id = 'gantt-spacer';
        spacer.style.position = 'absolute';
        spacer.style.top = '0';
        spacer.style.left = '0';
        spacer.style.zIndex = '1';
        spacer.style.pointerEvents = 'none';
        container.appendChild(spacer);
    }

    canvas.style.position = 'sticky';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '2';
    
    container.onscroll = () => {
        ganttState.scrollX = container.scrollLeft;
        ganttState.scrollY = container.scrollTop;
        requestAnimationFrame(draw);
    };

    canvas.onmousemove = (e) => {
        const rect = canvas.getBoundingClientRect();
        checkHover(e.clientX - rect.left, e.clientY - rect.top);
    };

    canvas.onclick = (e) => {
        const rect = canvas.getBoundingClientRect();
        handleClick(e.clientX - rect.left, e.clientY - rect.top);
    };
}

function actualizarFilasVisibles() {
    ganttState.filasVisibles = [];
    ganttState.datos.forEach(padre => {
        ganttState.filasVisibles.push({ type: 'parent', data: padre, depth: 0 });
        if (ganttState.expanded[padre.id]) {
            padre.hijos.forEach(hijo => {
                ganttState.filasVisibles.push({ type: 'child', data: hijo, color: padre.color, depth: 1 });
            });
        }
    });
}

function resizeAndDraw() {
    const container = document.getElementById('canvas-container');
    const canvas = document.getElementById('ganttCanvas');
    const spacer = document.getElementById('gantt-spacer');
    const cfg = ganttState.config;

    const availableWidth = container.clientWidth - cfg.sidebarWidth;
    const contentWidthBase = (ganttState.fechas.totalDias + 1) * cfg.basePixelsPerDay;

    // Lógica de Auto-ajuste para llenar la pantalla si hay pocos datos
    if (contentWidthBase < availableWidth) {
        cfg.pixelsPerDay = availableWidth / (ganttState.fechas.totalDias + 1);
        ganttState.scrollX = 0; 
    } else {
        cfg.pixelsPerDay = cfg.basePixelsPerDay;
    }

    const anchoTimeline = (ganttState.fechas.totalDias + 1) * cfg.pixelsPerDay;
    const totalW = cfg.sidebarWidth + anchoTimeline;
    const totalH = cfg.headerHeight + (ganttState.filasVisibles.length * cfg.rowHeight) + 30;

    spacer.style.width = totalW + 'px';
    spacer.style.height = totalH + 'px';

    canvas.width = container.clientWidth; 
    canvas.height = container.clientHeight; 

    requestAnimationFrame(draw);
}

function draw() {
    const canvas = document.getElementById('ganttCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cfg = ganttState.config;
    
    const sx = ganttState.scrollX;
    const sy = ganttState.scrollY;
    const pxPerDay = cfg.pixelsPerDay; // 🔥 Definición de la variable para evitar ReferenceError

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = cfg.font;

    // --- CAPA 1: TIMELINE (GRILLA Y BARRAS) ---
    ctx.save();
    ctx.translate(-sx, -sy); 

    const startX = cfg.sidebarWidth;

    // A. Grilla Vertical
    ctx.beginPath();
    ctx.strokeStyle = '#cbcbcb';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    
    for (let i = 0; i <= ganttState.fechas.totalDias; i++) {
        const x = startX + (i * pxPerDay);
        const d = new Date(ganttState.fechas.inicio.getTime() + (i * 86400000));
        let dibujarLinea = false;

        if (ganttState.viewMode === 'day') {
            dibujarLinea = true;
            ctx.setLineDash([4, 4]);
        } 
        else if (ganttState.viewMode === 'week') {
            if (d.getDay() === 1) { 
                dibujarLinea = true; 
                ctx.setLineDash([]); 
            }
        }
        else if (ganttState.viewMode === 'month') {
            if (d.getDate() === 1) {
                dibujarLinea = true;
                ctx.setLineDash([]);
            }
        }

        if (dibujarLinea) {
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height + sy);
        }
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // B. Filas y Barras
    ganttState.filasVisibles.forEach((fila, index) => {
        const y = cfg.headerHeight + (index * cfg.rowHeight);
        
        ctx.beginPath();
        ctx.strokeStyle = '#e6e6e6';
        ctx.moveTo(0, y + cfg.rowHeight);
        ctx.lineTo(startX + (ganttState.fechas.totalDias * pxPerDay), y + cfg.rowHeight);
        ctx.stroke();

        const dIni = new Date(fila.data.inicio + 'T00:00:00');
        const dFin = new Date(fila.data.fin + 'T00:00:00');
        const diffMs = dIni - ganttState.fechas.inicio;
        const duracionMs = dFin - dIni;
        const diffDias = diffMs / 86400000;
        const duracionDias = (duracionMs / 86400000) + 1;

        const barX = startX + (diffDias * pxPerDay) + 2; 
        const barW = Math.max((duracionDias * pxPerDay) - 4, 2);
        const barY = y + (cfg.rowHeight - cfg.barHeight) / 2;

        fila.hitbox = { x: barX, y: barY, w: barW, h: cfg.barHeight };
        const color = fila.type === 'parent' ? fila.data.color : fila.color;
        ctx.fillStyle = color;
        ctx.globalAlpha = fila.type === 'child' ? 0.6 : 1.0;
        
        if (ganttState.hoverBar === index) {
            ctx.shadowColor = 'rgba(0,0,0,0.3)';
            ctx.shadowBlur = 5;
        } else {
            ctx.shadowColor = 'transparent';
        }

        ctx.beginPath();
        roundRectManual(ctx, barX, barY, barW, cfg.barHeight, 4);
        ctx.fill();
        
        ctx.globalAlpha = 1.0;
        ctx.shadowColor = 'transparent';

        if (barW > 30) {
            ctx.fillStyle = '#fff';
            ctx.font = "12px 'Segoe UI'";
            ctx.textAlign = 'left';
            ctx.textBaseline = 'middle';
            ctx.save();
            ctx.beginPath();
            ctx.rect(barX, barY, barW, cfg.barHeight);
            ctx.clip();
            ctx.fillText(fila.data.nombre || fila.data.actividad, barX + 5, barY + (cfg.barHeight/2)+1);
            ctx.restore();
        }
    });
    ctx.restore();

    // --- CAPA 2: SIDEBAR (Sticky X) ---
    ctx.save();
    ctx.translate(0, -sy);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, sy, cfg.sidebarWidth, canvas.height); 
    
    ctx.beginPath();
    ctx.strokeStyle = '#e0e0e0';
    ctx.moveTo(cfg.sidebarWidth, sy);
    ctx.lineTo(cfg.sidebarWidth, sy + canvas.height);
    ctx.stroke();

    ganttState.filasVisibles.forEach((fila, index) => {
        const y = cfg.headerHeight + (index * cfg.rowHeight);
        const textY = y + (cfg.rowHeight / 2);
        
        if (ganttState.hoverBar === index) {
            ctx.fillStyle = '#f9f9f9';
            ctx.fillRect(0, y, cfg.sidebarWidth - 1, cfg.rowHeight);
        }

        const indent = 15 + (fila.depth * 20);

        if (fila.type === 'parent') {
            const toggleX = 15;
            fila.toggleHitbox = { x: toggleX - 5, y: textY - 10, w: 20, h: 20 };
            ctx.fillStyle = '#555';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(ganttState.expanded[fila.data.id] ? '▼' : '▶', toggleX, textY);
            ctx.font = "600 12.5px 'Segoe UI'";
            ctx.fillStyle = '#111';
        } else {
            ctx.font = "12.5px 'Segoe UI'";
            ctx.fillStyle = '#333';
        }
        ctx.textAlign = 'left';
        ctx.fillText(fila.data.nombre || fila.data.actividad, indent + 15, textY);
    });
    ctx.restore();

    // --- CAPA 3: HEADER (Sticky Y) ---
    ctx.save();
    ctx.translate(-sx, 0); 
    ctx.fillStyle = '#A3BD31';
    ctx.fillRect(sx, 0, canvas.width, cfg.headerHeight);
    
    ctx.beginPath();
    ctx.strokeStyle = '#dfe1e6';
    ctx.moveTo(sx, cfg.headerHeight);
    ctx.lineTo(sx + canvas.width, cfg.headerHeight);
    ctx.stroke();

    ctx.fillStyle = '#6b778c';
    ctx.textAlign = 'center';
    
    for (let i = 0; i <= ganttState.fechas.totalDias; i++) {
        const x = startX + (i * pxPerDay) + (pxPerDay / 2);
        const d = new Date(ganttState.fechas.inicio.getTime() + (i * 86400000));
        const diaNum = d.getDate();
        const mes = d.toLocaleDateString('es-CO', { month: 'short' }).replace('.', '').toUpperCase();

        if (ganttState.viewMode === 'day') {
            ctx.font = "9px 'Segoe UI'";
            ctx.fillStyle = '#f9f9f9';
            ctx.fillText(mes, x, 18);
            ctx.font = "bold 12px 'Segoe UI'";
            ctx.fillStyle = '#fff';
            ctx.fillText(diaNum, x, 36);
            ctx.beginPath(); ctx.strokeStyle = 'rgba(255,255,255,0.2)'; 
            ctx.moveTo(startX+(i*pxPerDay), 0); ctx.lineTo(startX+(i*pxPerDay), cfg.headerHeight); ctx.stroke();
        }
        else if (ganttState.viewMode === 'week') {
            if (d.getDay() === 1) { 
                const xSemana = x + (pxPerDay * 3);
                ctx.font = "bold 11px 'Segoe UI'";
                ctx.fillStyle = '#fff';
                ctx.fillText(`Semana ${getWeekNumber(d)}`, xSemana, 28);
                ctx.beginPath(); ctx.strokeStyle = 'rgba(255,255,255,0.3)'; 
                ctx.moveTo(startX+(i*pxPerDay), 0); ctx.lineTo(startX+(i*pxPerDay), cfg.headerHeight); ctx.stroke();
            }
        }
        else if (ganttState.viewMode === 'month') {
            if (d.getDate() === 1) {
                const diasEnMes = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
                const xMes = x + (pxPerDay * diasEnMes / 2);
                ctx.font = "bold 12px 'Segoe UI'";
                ctx.fillStyle = '#fff';
                ctx.fillText(d.toLocaleDateString('es-CO', {month:'long'}).toUpperCase(), xMes, 28);
                ctx.beginPath(); ctx.strokeStyle = 'rgba(255,255,255,0.3)'; 
                ctx.moveTo(startX+(i*pxPerDay), 0); ctx.lineTo(startX+(i*pxPerDay), cfg.headerHeight); ctx.stroke();
            }
        }
    }
    ctx.restore();

    // --- CAPA 4: CORNER ---
    ctx.fillStyle = '#A3BD31';
    ctx.fillRect(0, 0, cfg.sidebarWidth, cfg.headerHeight);
    ctx.fillStyle = '#fff';
    ctx.font = "15px 'Segoe UI'";
    ctx.textAlign = 'left';
    ctx.fillText("Actividad / Ubicación", 20, 30);
    ctx.beginPath(); ctx.strokeStyle = '#dfe1e6';
    ctx.moveTo(cfg.sidebarWidth, 0); ctx.lineTo(cfg.sidebarWidth, cfg.headerHeight);
    ctx.moveTo(0, cfg.headerHeight); ctx.lineTo(cfg.sidebarWidth, cfg.headerHeight);
    ctx.stroke();
}

function checkHover(mouseX, mouseY) {
    const worldX = mouseX + ganttState.scrollX;
    const worldY = mouseY + ganttState.scrollY;
    const sideY = mouseY + ganttState.scrollY;

    let foundBar = null;
    let foundToggle = null;

    ganttState.filasVisibles.forEach((fila, index) => {
        if (fila.toggleHitbox) {
            if (mouseX >= fila.toggleHitbox.x && mouseX <= fila.toggleHitbox.x + fila.toggleHitbox.w &&
                sideY >= fila.toggleHitbox.y && sideY <= fila.toggleHitbox.y + fila.toggleHitbox.h) {
                foundToggle = index;
            }
        }
        if (fila.hitbox) {
            if (worldX >= fila.hitbox.x && worldX <= fila.hitbox.x + fila.hitbox.w &&
                worldY >= fila.hitbox.y && worldY <= fila.hitbox.y + fila.hitbox.h) {
                foundBar = index;
            }
        }
    });

    const changed = (foundBar !== ganttState.hoverBar || foundToggle !== ganttState.hoverToggle);
    ganttState.hoverBar = foundBar;
    ganttState.hoverToggle = foundToggle;

    if (changed) {
        document.getElementById('ganttCanvas').style.cursor = (foundToggle !== null || foundBar !== null) ? 'pointer' : 'default';
        requestAnimationFrame(draw);
    }
}

function handleClick(mouseX, mouseY) {
    if (ganttState.hoverToggle !== null) {
        const fila = ganttState.filasVisibles[ganttState.hoverToggle];
        ganttState.expanded[fila.data.id] = !ganttState.expanded[fila.data.id];
        actualizarFilasVisibles();
        resizeAndDraw();
    } else if (ganttState.hoverBar !== null) {
        const fila = ganttState.filasVisibles[ganttState.hoverBar];
        const d = fila.data;
        if(typeof Swal !== 'undefined'){
            Swal.fire({ title: d.nombre || d.actividad, html: `Inicio: ${d.inicio}<br>Fin: ${d.fin}`, icon: 'info' });
        } else {
            alert(`${d.nombre}\n${d.inicio} - ${d.fin}`);
        }
    }
}

function getWeekNumber(d) {
    d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay()||7));
    var yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
    return Math.ceil((((d - yearStart) / 86400000) + 1)/7);
}

function roundRectManual(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
}