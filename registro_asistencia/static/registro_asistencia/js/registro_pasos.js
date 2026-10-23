// Los nombres y textos que vienen del servidor se escapan antes de insertarlos con innerHTML (evita XSS)
function escaparHTML(texto) {
    return String(texto).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================
    // 🌍 LÓGICA UNIVERSAL (PANEL IZQUIERDO Y OJITO)
    // =========================================================
    const buscadorInput = document.getElementById('buscador-empleados');
    const checkSeleccionarTodos = document.getElementById('check-seleccionar-todos');
    const filasEmpleados = document.querySelectorAll('.empleado-fila');
    const checksEmpleados = document.querySelectorAll('.check-empleado');
    const contadorCaja = document.getElementById('contador-seleccionados-box');
    const contadorFooter = document.getElementById('contador-asignados');
    const listaConfirmados = document.querySelector('.rp-confirmed-list');
    const btnSiguiente = document.getElementById('btn-siguiente-paso1'); 

    // Detectamos inteligentemente en qué paso estamos leyendo el título
    const tituloPasoText = document.querySelector('.rp-step-title') ? document.querySelector('.rp-step-title').textContent : '';
    const esPaso1 = document.querySelector('.rp-novedades-grid') !== null;
    const esPaso2 = document.querySelector('.rp-reloj-wrapper') !== null && tituloPasoText.includes('Paso 2');
    const esPaso3 = document.querySelector('.rp-reloj-wrapper') !== null && tituloPasoText.includes('Paso 3');

    // Lo que se asignó antes en este paso (al volver con "Atrás"): {id_empleado: valor}
    const previasTag = document.getElementById('asignaciones-previas');
    const asignacionesPrevias = previasTag ? JSON.parse(previasTag.textContent) : {};

    // Empleados que ya tienen entradas y salidas múltiples: si cambia su hora de entrada o de salida, se eliminan
    const multiplesTag = document.getElementById('con-multiples');
    const empleadosConMultiples = multiplesTag ? JSON.parse(multiplesTag.textContent) : [];

    function restaurarAsignaciones(agregarChip) {
        Object.entries(asignacionesPrevias).forEach(([idEmp, valor]) => {
            const check = document.querySelector(`.check-empleado[value="${idEmp}"]`);
            if (check) agregarChip(check, valor);
        });
    }

    // 1. Buscador
    if (buscadorInput) {
        buscadorInput.addEventListener('keyup', function() {
            const textoBusqueda = this.value.toLowerCase();
            filasEmpleados.forEach(fila => {
                if (fila.classList.contains('ya-asignado')) return;
                const nombreEmpleado = fila.querySelector('.nombre-empleado-texto').textContent.toLowerCase();
                fila.style.display = nombreEmpleado.includes(textoBusqueda) ? 'flex' : 'none';
            });
        });
    }

    // 2. Seleccionar todos
    if (checkSeleccionarTodos) {
        checkSeleccionarTodos.addEventListener('change', function() {
            const estaMarcado = this.checked;
            filasEmpleados.forEach(fila => {
                if (fila.style.display !== 'none') {
                    const checkbox = fila.querySelector('.check-empleado');
                    if (checkbox) checkbox.checked = estaMarcado;
                }
            });
            actualizarContadoresIzquierda();
        });
    }

    checksEmpleados.forEach(check => {
        check.addEventListener('change', actualizarContadoresIzquierda);
    });

    function actualizarContadoresIzquierda() {
        const total = document.querySelectorAll('.check-empleado:checked').length;
        if (contadorCaja) contadorCaja.textContent = total;
    }

    // 3. Modal de Revisión (El Ojito Universal)
    const btnOjito = document.querySelector('.rp-btn-hide');
    const modalRevision = document.getElementById('modal-revision');
    const modalContenido = document.getElementById('modal-revision-contenido');
    const btnGuardarModal = document.getElementById('btn-guardar-modal');
    const modalTitulo = document.getElementById('modal-revision-titulo');
    const modalColumnaDer = document.getElementById('modal-revision-columna-der');
    
    const buscadorModal = document.getElementById('buscador-modal');

    // Buscador del modal: filtra por nombre, sin distinguir mayúsculas ni tildes
    function normalizarTexto(texto) {
        return texto.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    }

    function filtrarModal() {
        const termino = normalizarTexto(buscadorModal.value.trim());
        let visibles = 0;
        modalContenido.querySelectorAll('.modal-fila-emp').forEach(fila => {
            const coincide = normalizarTexto(fila.querySelector('.modal-nombre-emp').textContent).includes(termino);
            fila.style.display = coincide ? 'flex' : 'none';
            if (coincide) visibles++;
        });

        let aviso = document.getElementById('modal-sin-resultados');
        if (modalContenido.querySelector('.modal-fila-emp') && visibles === 0) {
            if (!aviso) {
                aviso = document.createElement('p');
                aviso.id = 'modal-sin-resultados';
                aviso.style.cssText = 'text-align:center; padding: 20px; color:#999;';
                aviso.textContent = 'No se encontraron empleados.';
                modalContenido.appendChild(aviso);
            }
        } else if (aviso) {
            aviso.remove();
        }
    }

    if (buscadorModal) buscadorModal.addEventListener('input', filtrarModal);

    if (btnOjito) {
        btnOjito.addEventListener('click', function() {
            modalContenido.innerHTML = '';
            if (buscadorModal) buscadorModal.value = '';
            const chips = listaConfirmados.querySelectorAll('.chip-confirmado');
            
            if (esPaso1) {
                modalTitulo.textContent = "Revisión y edición: Novedades";
                modalColumnaDer.textContent = "Novedad asignada";
            } else if (esPaso2) {
                modalTitulo.textContent = "Revisión y edición: Hora de entrada";
                modalColumnaDer.textContent = "Hora asignada";
            } else if (esPaso3) {
                modalTitulo.textContent = "Revisión y edición: Hora de salida";
                modalColumnaDer.textContent = "Hora asignada";
            }

            if (chips.length === 0) {
                modalContenido.innerHTML = '<p style="text-align:center; padding: 20px; color:#999;">No hay empleados confirmados aún.</p>';
            } else {
                chips.forEach((chip, index) => {
                    const idEmp = chip.querySelector('input[name="empleados_confirmados[]"]').value;
                    const nombreEmp = chip.querySelector('strong').textContent;
                    const bgRow = (index % 2 === 0) ? '#ffffff' : '#f9f9f9';
                    
                    let controlHTML = '';
                    
                    if (esPaso1) {
                        const novedadActual = chip.querySelector(`input[name="novedad_${idEmp}"]`).value;
                        const listadoNovedades = [
                            {val: 'asistencia_normal', txt: 'Asistencia normal'}, {val: 'ausentismo', txt: 'Ausentismo'},
                            {val: 'sancion', txt: 'Sanción'}, {val: 'incapacidad_general', txt: 'Incapacidad general'},
                            {val: 'incapacidad_trabajo', txt: 'Incapacidad de trabajo'}, {val: 'permiso_no_remunerado', txt: 'Permiso no remunerado'},
                            {val: 'permiso_remunerado', txt: 'Permiso remunerado'}, {val: 'licencia', txt: 'Licencia'},
                            {val: 'vacaciones', txt: 'Vacaciones'}, {val: 'retirado', txt: 'Retirado'}, {val: 'descanso', txt: 'Descanso'}
                        ];
                        let opciones = '';
                        listadoNovedades.forEach(nov => {
                            const sel = (nov.val === novedadActual) ? 'selected' : '';
                            opciones += `<option value="${nov.val}" ${sel}>${nov.txt}</option>`;
                        });
                        controlHTML = `<select class="select-modal-edit" data-id="${idEmp}" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;">${opciones}</select>`;
                    } 
                    else if (esPaso2 || esPaso3) {
                        const sufijo = esPaso2 ? 'inicio' : 'salida';
                        const horaActual = chip.querySelector(`input[name="hora_${sufijo}_${idEmp}"]`).value;
                        controlHTML = `<input type="text" class="input-modal-edit" data-id="${idEmp}" value="${escaparHTML(horaActual)}" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc; width: 90px; text-align: center;">`;
                    }

                    modalContenido.innerHTML += `
                        <div class="modal-fila-emp" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background-color: ${bgRow}; border-bottom: 1px solid #eee;">
                            <div style="display: flex; align-items: center; gap: 12px; color: #333;">
                                <i class="fa-regular fa-user" style="font-size: 18px; color: #444;"></i>
                                <span class="modal-nombre-emp" style="font-weight: bold;">${escaparHTML(nombreEmp)}</span>
                            </div>
                            <div>${controlHTML}</div>
                        </div>
                    `;
                });
            }
            modalRevision.style.display = 'flex';
        });
    }

    if (btnGuardarModal) {
        btnGuardarModal.addEventListener('click', async function() {
            const controles = modalContenido.querySelectorAll('.select-modal-edit, .input-modal-edit');

            // Cambiar la hora de entrada o de salida de alguien con entradas y salidas múltiples las elimina: se avisa antes
            if (esPaso2 || esPaso3) {
                const sufijo = esPaso2 ? 'inicio' : 'salida';
                const afectados = Array.from(controles).filter(control => {
                    const idEmp = control.getAttribute('data-id');
                    return empleadosConMultiples.includes(idEmp)
                        && control.value !== document.querySelector(`input[name="hora_${sufijo}_${idEmp}"]`).value;
                }).map(control => control.closest('.modal-fila-emp').querySelector('.modal-nombre-emp').textContent);
                if (afectados.length && !await Avisos.confirmarEliminarMultiples(afectados)) return;
            }

            controles.forEach(control => {
                const idEmp = control.getAttribute('data-id');
                const nuevoValor = control.value;

                if (esPaso1) {
                    const textoVisual = control.options[control.selectedIndex].text;
                    document.querySelector(`input[name="novedad_${idEmp}"]`).value = nuevoValor;
                    document.querySelector(`input[name="novedad_${idEmp}"]`).closest('.chip-confirmado').querySelector('.texto-novedad').textContent = `(${textoVisual})`;
                } else if (esPaso2 || esPaso3) {
                    const sufijo = esPaso2 ? 'inicio' : 'salida';
                    const preTexto = esPaso2 ? 'Entrada' : 'Salida';
                    document.querySelector(`input[name="hora_${sufijo}_${idEmp}"]`).value = nuevoValor;
                    document.querySelector(`input[name="hora_${sufijo}_${idEmp}"]`).closest('.chip-confirmado').querySelector('span').textContent = `(${preTexto}: ${nuevoValor})`;
                }
            });
            modalRevision.style.display = 'none'; 
        });
    }

    // ==========================================
    // 🟢 PASO 1: NOVEDADES (Lógica de asignación)
    // ==========================================
    if (esPaso1) {
        const botonesAsignar = document.querySelectorAll('.rp-btn-asignar');
        const nombresNovedad = {};      // código -> texto de la tarjeta, para rearmar los chips al volver
        botonesAsignar.forEach(boton => {
            nombresNovedad[boton.dataset.novedad] = boton.previousElementSibling.textContent.trim().replace(/\s+/g, ' ');
        });

        function agregarChipNovedad(check, codigoNovedad) {
            const nombreNovedad = nombresNovedad[codigoNovedad];
            const fila = check.closest('.empleado-fila');
            const chip = document.createElement('div');
            chip.className = 'chip-confirmado';
            chip.style.cssText = "display: inline-flex; align-items: center; background: #f1f3f5; padding: 6px 12px; border-radius: 20px; margin: 5px; font-size: 14px; border: 1px solid #dee2e6;";
            chip.innerHTML = `
                <strong>${escaparHTML(fila.querySelector('.nombre-empleado-texto').textContent)}</strong> &nbsp; <span class="texto-novedad" style="color: #666;">(${escaparHTML(nombreNovedad)})</span>
                <i class="fas fa-times-circle btn-quitar-chip" style="margin-left: 10px; cursor: pointer; color: #dc3545;"></i>
                <input type="hidden" name="empleados_confirmados[]" value="${check.value}">
                <input type="hidden" name="novedad_${check.value}" value="${codigoNovedad}">
            `;
            chip.querySelector('.btn-quitar-chip').addEventListener('click', function() {
                chip.remove(); fila.classList.remove('ya-asignado'); fila.style.display = 'flex'; actualizarContadoresIzquierda(); validarAvance();
            });
            listaConfirmados.appendChild(chip);
            fila.classList.add('ya-asignado'); fila.style.display = 'none'; check.checked = false;
        }

        botonesAsignar.forEach(boton => {
            boton.addEventListener('click', function() {
                const seleccionados = document.querySelectorAll('.check-empleado:checked');
                if (seleccionados.length === 0) return alert('⚠️ Selecciona un empleado.');

                seleccionados.forEach(check => agregarChipNovedad(check, this.getAttribute('data-novedad')));
                if (checkSeleccionarTodos) checkSeleccionarTodos.checked = false;
                actualizarContadoresIzquierda(); validarAvance();
            });
        });

        restaurarAsignaciones((check, codigo) => { if (nombresNovedad[codigo]) agregarChipNovedad(check, codigo); });
        validarAvance();
    }

    // ==========================================
    // 🟡 PASOS 2 y 3: RELOJ INTELIGENTE
    // ==========================================
    if (esPaso2 || esPaso3) {
        const botonesRapidos = document.querySelectorAll('.rp-quick-btn');
        const btnAsignarReloj = document.querySelector('.rp-btn-asignar-reloj');
        const botonesAmPm = document.querySelectorAll('.rp-ampm-btn');
        
        // Variables dinámicas según el paso
        const preTexto = esPaso2 ? 'Entrada' : 'Salida';
        const inputNameSufijo = esPaso2 ? 'inicio' : 'salida';

        // 1. Convertir los números en campos de texto inteligentes (Regla 12h)
        const digitosReloj = [
            document.getElementById('hora-decena'),
            document.getElementById('hora-unidad'),
            document.getElementById('min-decena'),
            document.getElementById('min-unidad')
        ];

        digitosReloj.forEach((digito, index) => {
            if (!digito) return;
            
            digito.setAttribute('contenteditable', 'true');
            digito.style.outline = 'none';
            digito.style.cursor = 'text';

            digito.addEventListener('focus', function() {
                const range = document.createRange();
                range.selectNodeContents(this);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            });

            digito.addEventListener('keydown', function(e) {
                if (['Backspace', 'Tab', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;
                if (!/^[0-9]$/.test(e.key)) {
                    e.preventDefault();
                    return;
                }

                e.preventDefault();
                const num = parseInt(e.key);

                if (index === 0) { 
                    if (num >= 2) {
                        this.textContent = '0';
                        digitosReloj[1].textContent = num.toString();
                        digitosReloj[2].focus();
                    } else {
                        this.textContent = num.toString();
                        digitosReloj[1].focus();
                    }
                } 
                else if (index === 1) { 
                    const decena = parseInt(digitosReloj[0].textContent) || 0;
                    if (decena === 1 && num > 2) return; 
                    if (decena === 0 && num === 0) return; 
                    
                    this.textContent = num.toString();
                    digitosReloj[2].focus();
                } 
                else if (index === 2) { 
                    if (num > 5) return; 
                    this.textContent = num.toString();
                    digitosReloj[3].focus();
                } 
                else if (index === 3) { 
                    this.textContent = num.toString();
                    this.blur(); 
                }
            });

            digito.addEventListener('blur', function() {
                if (this.textContent.trim() === '') this.textContent = '0';
                if (index === 1 && digitosReloj[0].textContent === '0' && this.textContent === '0') {
                    this.textContent = '1';
                }
            });
        });

        // 2. Función maestra de asignación dinámica
        function agregarChipHora(check, horaTexto) {
            const fila = check.closest('.empleado-fila');
            const chip = document.createElement('div');
            chip.className = 'chip-confirmado';
            chip.style.cssText = "display: inline-flex; align-items: center; background: #f1f3f5; padding: 6px 12px; border-radius: 20px; margin: 5px; font-size: 14px; border: 1px solid #dee2e6;";

            chip.innerHTML = `
                <strong>${escaparHTML(fila.querySelector('.nombre-empleado-texto').textContent)}</strong> &nbsp; <span style="color: #666;">(${escaparHTML(preTexto)}: ${escaparHTML(horaTexto)})</span>
                <i class="fas fa-times-circle btn-quitar-chip" style="margin-left: 10px; cursor: pointer; color: #dc3545;"></i>
                <input type="hidden" name="empleados_confirmados[]" value="${check.value}">
                <input type="hidden" name="hora_${inputNameSufijo}_${check.value}" value="${escaparHTML(horaTexto)}">
            `;

            chip.querySelector('.btn-quitar-chip').addEventListener('click', function() {
                chip.remove(); fila.classList.remove('ya-asignado'); fila.style.display = 'flex'; actualizarContadoresIzquierda(); validarAvance();
            });
            listaConfirmados.appendChild(chip);
            fila.classList.add('ya-asignado'); fila.style.display = 'none'; check.checked = false;
        }

        async function procesarAsignacionHora(horaTexto) {
            const seleccionados = document.querySelectorAll('.check-empleado:checked');
            if (seleccionados.length === 0) return alert('⚠️ Selecciona un empleado de la lista primero.');

            const afectados = Array.from(seleccionados).filter(check =>
                empleadosConMultiples.includes(check.value)
                && asignacionesPrevias[check.value] && asignacionesPrevias[check.value] !== horaTexto);
            if (afectados.length && !await Avisos.confirmarEliminarMultiples(
                afectados.map(check => check.closest('.empleado-fila').querySelector('.nombre-empleado-texto').textContent))) return;

            seleccionados.forEach(check => agregarChipHora(check, horaTexto));
            if (checkSeleccionarTodos) checkSeleccionarTodos.checked = false;
            actualizarContadoresIzquierda(); validarAvance();
        }

        restaurarAsignaciones(agregarChipHora);
        validarAvance();

        // 3. Activar botones
        botonesRapidos.forEach(b => b.addEventListener('click', function() { procesarAsignacionHora(this.textContent.trim()); }));
        
        botonesAmPm.forEach(boton => {
            boton.addEventListener('click', function() {
                botonesAmPm.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
            });
        });

        if (btnAsignarReloj) {
            btnAsignarReloj.addEventListener('click', function() {
                const hDecena = document.getElementById('hora-decena').textContent.trim();
                const hUnidad = document.getElementById('hora-unidad').textContent.trim();
                const mDecena = document.getElementById('min-decena').textContent.trim();
                const mUnidad = document.getElementById('min-unidad').textContent.trim();
                const amPmTexto = document.querySelector('.rp-ampm-btn.active') ? document.querySelector('.rp-ampm-btn.active').textContent.trim() : 'A.M';
                
                procesarAsignacionHora(`${hDecena}${hUnidad}:${mDecena}${mUnidad} ${amPmTexto}`);
            });
        }
    }

    // ==========================================
    // 🔒 Función universal avance
    // ==========================================
    function validarAvance() {
        const cantidadAsignados = document.querySelectorAll('.chip-confirmado').length;
        const totalEmpleados = document.querySelectorAll('.empleado-fila').length; 
        if (contadorFooter) contadorFooter.textContent = cantidadAsignados;

        if (btnSiguiente) {
            const iconoSiguiente = btnSiguiente.querySelector('.material-symbols-outlined');
            if (cantidadAsignados > 0 && cantidadAsignados === totalEmpleados) {
                btnSiguiente.classList.remove('locked'); btnSiguiente.disabled = false; 
                if (iconoSiguiente) iconoSiguiente.textContent = 'arrow_forward';
            } else {
                btnSiguiente.classList.add('locked'); btnSiguiente.disabled = true; 
                if (iconoSiguiente) iconoSiguiente.textContent = 'lock';
            }
        }
    }
});