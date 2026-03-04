from django.shortcuts import render

def entrada_salida_personal(request):
    return render(request, 'entrada_y_salida_del_personal/entrada_salida_personal.html')
