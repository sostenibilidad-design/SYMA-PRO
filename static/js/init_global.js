// Valor de una cookie (p. ej. csrftoken); lo usan los scripts que hacen fetch con POST
function getCookie(nombre) {
    const par = document.cookie.split('; ').find(c => c.startsWith(nombre + '='));
    return par ? decodeURIComponent(par.split('=')[1]) : '';
}

function inicializarModalActualizar(contenedor) {
    console.log("Inicializando modal de ACTUALIZAR/REGISTRAR en contenedor:", contenedor);
    inicializarComportamientos(contenedor);
}

function inicializarComportamientos(contenedor) {
    inicializarModales(contenedor);
    if (typeof inicializarDespliegue === "function") {
        inicializarDespliegue(contenedor);
    }
    if (typeof inicializarActualizarCuadrilla === "function") {
        inicializarActualizarCuadrilla(contenedor);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    inicializarComportamientos(document);
});

window.inicializarModalActualizar = inicializarModalActualizar;
