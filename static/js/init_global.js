function inicializarModalActualizar(contenedor) {
    console.log("Inicializando modal de ACTUALIZAR/REGISTRAR en contenedor:", contenedor);
    inicializarComportamientos(contenedor);
}

function inicializarComportamientos(contenedor) {
    inicializarModales(contenedor);
    inicializarDespliegue(contenedor);
    inicializarActualizarCuadrilla(contenedor) ;
}

document.addEventListener("DOMContentLoaded", () => {
    inicializarComportamientos(document);
});

window.inicializarModalActualizar = inicializarModalActualizar;
