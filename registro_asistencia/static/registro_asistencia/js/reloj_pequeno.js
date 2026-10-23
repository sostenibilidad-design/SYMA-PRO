window.RelojPequeno = (function () {
    'use strict';

    // "HH:MM" 24 h -> "hh:mm A.M"
    function a12h(hhmm) {
        const [h, m] = hhmm.split(':').map(Number);
        const sufijo = h >= 12 ? 'P.M' : 'A.M';
        const h12 = h % 12 === 0 ? 12 : h % 12;
        return String(h12).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ' ' + sufijo;
    }

    // Lee un reloj y lo devuelve en 24 h ("HH:MM"), o null si no es una hora válida
    function leer(reloj) {
        const d = Array.from(reloj.querySelectorAll('.rc-digito')).map(el => el.textContent.trim() || '0');
        let horas = parseInt(d[0] + d[1], 10);
        const minutos = parseInt(d[2] + d[3], 10);
        if (isNaN(horas) || isNaN(minutos) || horas < 1 || horas > 12 || minutos > 59) return null;
        const pm = reloj.querySelector('.rc-ampm__btn.active').dataset.value === 'PM';
        if (pm && horas !== 12) horas += 12;
        if (!pm && horas === 12) horas = 0;
        return String(horas).padStart(2, '0') + ':' + String(minutos).padStart(2, '0');
    }

    // Pone una hora 24 h ("HH:MM") en el reloj
    function poner(reloj, hhmm) {
        const [h, m] = hhmm.split(':').map(Number);
        const h12 = h % 12 === 0 ? 12 : h % 12;
        const texto = String(h12).padStart(2, '0') + String(m).padStart(2, '0');
        reloj.querySelectorAll('.rc-digito').forEach((el, i) => { el.textContent = texto[i]; });
        const valor = h >= 12 ? 'PM' : 'AM';
        reloj.querySelectorAll('.rc-ampm__btn').forEach(b => b.classList.toggle('active', b.dataset.value === valor));
    }

    // Activa todos los relojes dentro de `contenedor` (los que ya estaban activos se saltan).
    // `alCambiar(reloj)` se llama cada vez que la persona edita una hora.
    function iniciar(contenedor, alCambiar) {
        contenedor.querySelectorAll('.rc-reloj').forEach(function (reloj) {
            if (reloj.dataset.listo) return;
            reloj.dataset.listo = '1';

            const digitos = Array.from(reloj.querySelectorAll('.rc-digito'));
            const avisar = () => { if (alCambiar) alCambiar(reloj); };

            digitos.forEach(function (digito, i) {
                digito.setAttribute('contenteditable', 'true');

                digito.addEventListener('focus', function () {
                    const rango = document.createRange();
                    rango.selectNodeContents(this);
                    const sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(rango);
                });

                digito.addEventListener('keydown', function (e) {
                    if (['Backspace', 'Tab', 'ArrowLeft', 'ArrowRight'].includes(e.key)) return;
                    e.preventDefault();
                    if (!/^[0-9]$/.test(e.key)) return;
                    const num = parseInt(e.key, 10);

                    if (i === 0) {
                        if (num >= 2) {                    // "7" se escribe como 07
                            this.textContent = '0';
                            digitos[1].textContent = String(num);
                            digitos[2].focus();
                        } else {
                            this.textContent = String(num);
                            digitos[1].focus();
                        }
                    } else if (i === 1) {
                        const decena = parseInt(digitos[0].textContent, 10) || 0;
                        if (decena === 1 && num > 2) return;   // máximo 12
                        if (decena === 0 && num === 0) return; // mínimo 01
                        this.textContent = String(num);
                        digitos[2].focus();
                    } else if (i === 2) {
                        if (num > 5) return;
                        this.textContent = String(num);
                        digitos[3].focus();
                    } else {
                        this.textContent = String(num);
                        this.blur();
                    }
                    avisar();
                });

                digito.addEventListener('blur', function () {
                    if (this.textContent.trim() === '') this.textContent = '0';
                    if (i === 1 && digitos[0].textContent === '0' && this.textContent === '0') this.textContent = '1';
                });
            });

            reloj.querySelectorAll('.rc-ampm__btn').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    reloj.querySelectorAll('.rc-ampm__btn').forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    avisar();
                });
            });
        });
    }

    return { a12h: a12h, leer: leer, poner: poner, iniciar: iniciar };
})();
