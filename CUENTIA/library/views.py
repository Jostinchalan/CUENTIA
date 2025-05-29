#library/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def generar_cuento_view(request):
    """Vista para generar stories"""
    if request.method == 'POST':
        # Aquí procesarás el formulario cuando esté listo
        titulo = request.POST.get('titulo')
        personaje = request.POST.get('personaje')
        tema = request.POST.get('tema')
        edad = request.POST.get('edad')
        longitud = request.POST.get('longitud')

        # Por ahora solo mostramos un mensaje
        from django.contrib import messages
        messages.success(request, f'Cuento "{titulo}" generado exitosamente!')

    return render(request, 'library/generar.html')

@login_required
def cuento_detalle(request, pk):
    """Vista para ver el detalle de un cuento (versión simplificada)"""
    return render(request, 'library/cuento_detalle.html', {'library': None})

@login_required
def audio_cuento(request, pk):
    """Vista para escuchar el audio de un cuento (versión simplificada)"""
    return render(request, 'library/audio.html', {'library': None})

@login_required
def biblioteca_view(request):
    """Vista para la biblioteca principal"""
    # Aquí puedes agregar la lógica para mostrar los cuentos guardados
    # Por ejemplo, obtener cuentos del usuario actual
    return render(request, 'library/biblioteca.html')

@login_required
def seguimiento_view(request):
    """Vista para el seguimiento lector"""
    return render(request, 'library/seguimiento.html')

@login_required
def generar_view(request):
    """Vista para generar cuentos (si es parte de library)"""
    return render(request, 'library/generar.html')