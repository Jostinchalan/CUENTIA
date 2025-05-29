# stories/views.py
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.core.exceptions import ValidationError
from .models import Cuento, EstadisticaLectura
from .services import openai_service
from .utils import generar_pdf_cuento
from user.models import Perfil
import threading
import time

logger = logging.getLogger(__name__)


@login_required
def generar_cuento_view(request):
    """Vista para el formulario de generación de cuentos"""
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            perfil_id = request.POST.get('perfil_id')
            titulo = request.POST.get('titulo', '').strip()
            personaje = request.POST.get('personaje', '').strip()
            nuevo_personaje = request.POST.get('nuevo_personaje', '').strip()
            tema = request.POST.get('tema', '').strip()
            nuevo_tema = request.POST.get('nuevo_tema', '').strip()
            edad = request.POST.get('edad', '')
            longitud = request.POST.get('longitud', '')
            guardar_datos = request.POST.get('guardar_datos') == 'on'

            # Determinar personaje y tema finales
            personaje_final = nuevo_personaje if personaje == 'nuevo' and nuevo_personaje else personaje
            tema_final = nuevo_tema if tema == 'nuevo' and nuevo_tema else tema

            # Validar datos del formulario
            datos_formulario = {
                'titulo': titulo,
                'personaje_principal': personaje_final,
                'tema': tema_final,
                'edad': edad,
                'longitud': longitud,
            }

            # Validaciones básicas
            if not datos_formulario['personaje_principal']:
                messages.error(request, 'El personaje principal es requerido.')
                return render(request, 'stories/generar.html', {
                    'perfiles': Perfil.objects.filter(usuario=request.user)
                })

            if not datos_formulario['tema']:
                messages.error(request, 'Debes seleccionar un tema.')
                return render(request, 'stories/generar.html', {
                    'perfiles': Perfil.objects.filter(usuario=request.user)
                })

            if not datos_formulario['edad']:
                messages.error(request, 'Debes seleccionar la edad del niño.')
                return render(request, 'stories/generar.html', {
                    'perfiles': Perfil.objects.filter(usuario=request.user)
                })

            if not datos_formulario['longitud']:
                messages.error(request, 'Debes seleccionar la longitud del cuento.')
                return render(request, 'stories/generar.html', {
                    'perfiles': Perfil.objects.filter(usuario=request.user)
                })

            # Guardar nuevos datos en el perfil si está marcado
            if guardar_datos and perfil_id:
                try:
                    perfil = Perfil.objects.get(id=perfil_id, usuario=request.user)

                    # Agregar nuevo personaje si no existe
                    if nuevo_personaje and nuevo_personaje not in perfil.personajes_lista():
                        if perfil.personajes_favoritos:
                            perfil.personajes_favoritos += f", {nuevo_personaje}"
                        else:
                            perfil.personajes_favoritos = nuevo_personaje

                    # Agregar nuevo tema si no existe
                    if nuevo_tema and nuevo_tema not in perfil.temas_lista():
                        if perfil.temas_preferidos:
                            perfil.temas_preferidos += f", {nuevo_tema}"
                        else:
                            perfil.temas_preferidos = nuevo_tema

                    perfil.save()
                    messages.success(request, f'Nuevos datos guardados en el perfil de {perfil.nombre}')

                except Perfil.DoesNotExist:
                    pass

            # Crear el cuento en estado "generando"
            cuento = Cuento.objects.create(
                usuario=request.user,
                titulo=datos_formulario['titulo'] or 'Cuento Mágico',
                personaje_principal=datos_formulario['personaje_principal'],
                tema=datos_formulario['tema'],
                edad=datos_formulario['edad'],
                longitud=datos_formulario['longitud'],
                estado='generando'
            )

            logger.info(f"Cuento creado con ID: {cuento.id} para usuario: {request.user.username}")

            # Iniciar generación inmediatamente en background
            def generar_en_background():
                try:
                    logger.info(f"Iniciando generacion de cuento ID: {cuento.id}")

                    # Generar el cuento completo con IA
                    titulo, contenido, moraleja, imagen_url, imagen_prompt = openai_service.generar_cuento_completo(
                        datos_formulario)

                    # Actualizar el cuento
                    cuento.titulo = titulo
                    cuento.contenido = contenido
                    cuento.moraleja = moraleja
                    cuento.imagen_url = imagen_url
                    cuento.imagen_prompt = imagen_prompt
                    cuento.estado = 'completado'

                    # Calcular tiempo estimado de lectura (aproximadamente 200 palabras por minuto)
                    palabras = len(contenido.split())
                    cuento.tiempo_lectura_estimado = max(60, (palabras / 200) * 60)  # mínimo 1 minuto

                    cuento.save()

                    logger.info(f"Cuento generado exitosamente: {titulo}")

                except Exception as e:
                    logger.error(f"Error generando cuento en background: {str(e)}")
                    cuento.estado = 'error'
                    cuento.save()

            # Iniciar thread
            thread = threading.Thread(target=generar_en_background)
            thread.daemon = True
            thread.start()

            # Guardar datos en sesión y redirigir
            request.session['datos_generacion'] = datos_formulario
            request.session['cuento_id'] = cuento.id

            return redirect('stories:generando')

        except Exception as e:
            logger.error(f"Error en generar_cuento_view: {str(e)}")
            messages.error(request, 'Ocurrió un error al procesar tu solicitud. Inténtalo de nuevo.')
            return render(request, 'stories/generar.html', {
                'perfiles': Perfil.objects.filter(usuario=request.user)
            })

    # GET request - mostrar formulario
    perfiles = Perfil.objects.filter(usuario=request.user)
    return render(request, 'stories/generar.html', {
        'perfiles': perfiles
    })


# ... resto de las vistas permanecen igual ...
@login_required
def generando_cuento_view(request):
    """Vista para la página de carga mientras se genera el cuento"""
    cuento_id = request.session.get('cuento_id')
    datos_formulario = request.session.get('datos_generacion')

    if not cuento_id or not datos_formulario:
        messages.error(request, 'No se encontraron datos de generación.')
        return redirect('stories:generar')

    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)

        logger.info(f"Estado actual del cuento {cuento.id}: {cuento.estado}")

        # Si el cuento ya está completado, redirigir inmediatamente
        if cuento.estado == 'completado':
            logger.info(f"Cuento {cuento.id} completado, redirigiendo...")
            # Limpiar sesión
            if 'cuento_id' in request.session:
                del request.session['cuento_id']
            if 'datos_generacion' in request.session:
                del request.session['datos_generacion']
            return redirect('stories:generated_story', cuento_id=cuento.id)

        # Si hay error, redirigir a generar
        if cuento.estado == 'error':
            logger.error(f"Cuento {cuento.id} tiene error")
            messages.error(request, 'Hubo un error generando el cuento. Inténtalo de nuevo.')
            return redirect('stories:generar')

        return render(request, 'stories/generando.html', {
            'cuento': cuento,
            'datos_formulario': datos_formulario
        })

    except Exception as e:
        logger.error(f"Error en generando_cuento_view: {str(e)}")
        messages.error(request, 'Ocurrió un error durante la generación.')
        return redirect('stories:generar')


@login_required
def check_cuento_status(request, cuento_id):
    """Vista AJAX para verificar el estado del cuento"""
    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)

        logger.info(f"Verificando estado del cuento {cuento_id}: {cuento.estado}")

        return JsonResponse({
            'estado': cuento.estado,
            'completado': cuento.estado == 'completado',
            'error': cuento.estado == 'error',
            'titulo': cuento.titulo,
            'debug_info': {
                'cuento_id': cuento.id,
                'usuario': cuento.usuario.username,
                'fecha_creacion': cuento.fecha_creacion.isoformat(),
                'contenido_length': len(cuento.contenido) if cuento.contenido else 0
            }
        })

    except Exception as e:
        logger.error(f"Error verificando estado del cuento {cuento_id}: {str(e)}")
        return JsonResponse({
            'estado': 'error',
            'completado': False,
            'error': True,
            'mensaje': str(e)
        })


@login_required
def generated_story_view(request, cuento_id):
    """Vista para mostrar el cuento generado"""
    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)

        logger.info(f"Mostrando cuento {cuento_id} con estado: {cuento.estado}")

        if cuento.estado == 'generando':
            return redirect('stories:generando')
        elif cuento.estado == 'error':
            messages.error(request, 'Hubo un error generando el cuento. Inténtalo de nuevo.')
            return redirect('stories:generar')

        # Marcar como leído
        cuento.marcar_como_leido()

        # Verificar que el cuento tenga contenido para TTS
        if not cuento.contenido or not cuento.contenido.strip():
            logger.warning(f"Cuento {cuento_id} no tiene contenido para TTS")

        # Registrar estadística de lectura
        EstadisticaLectura.objects.create(
            usuario=request.user,
            cuento=cuento,
            tipo_lectura='texto'
        )

        # Limpiar sesión
        if 'cuento_id' in request.session:
            del request.session['cuento_id']
        if 'datos_generacion' in request.session:
            del request.session['datos_generacion']

        return render(request, 'stories/generated_story.html', {
            'cuento': cuento
        })

    except Exception as e:
        logger.error(f"Error en generated_story_view: {str(e)}")
        messages.error(request, 'Ocurrió un error al cargar el cuento.')
        return redirect('stories:generar')


@login_required
def lista_cuentos_view(request):
    """Vista para listar todos los cuentos del usuario"""
    cuentos = Cuento.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')

    return render(request, 'stories/lista_cuentos.html', {
        'cuentos': cuentos
    })


@login_required
def descargar_pdf_view(request, cuento_id):
    """Vista para descargar el cuento en PDF"""
    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)

        # Generar PDF
        pdf_buffer = generar_pdf_cuento(cuento)

        # Crear respuesta HTTP
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{cuento.titulo}.pdf"'

        return response

    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        messages.error(request, 'Error al generar el PDF.')
        return redirect('stories:generated_story', cuento_id=cuento_id)


@login_required
@require_POST
def guardar_biblioteca_view(request, cuento_id):
    """Vista para guardar el cuento en la biblioteca"""
    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)

        # El cuento ya está guardado automáticamente, solo confirmar
        messages.success(request, f'¡Cuento "{cuento.titulo}" guardado en tu biblioteca!')

        # Redirigir a la biblioteca
        return redirect('library:biblioteca')

    except Exception as e:
        logger.error(f"Error guardando en biblioteca: {str(e)}")
        messages.error(request, 'Error al guardar en la biblioteca.')
        return redirect('stories:generated_story', cuento_id=cuento_id)


@login_required
@require_POST
def toggle_favorito_view(request, cuento_id):
    """Vista AJAX para alternar favorito"""
    try:
        cuento = get_object_or_404(Cuento, id=cuento_id, usuario=request.user)
        es_favorito = cuento.toggle_favorito()

        return JsonResponse({
            'success': True,
            'es_favorito': es_favorito,
            'message': 'Agregado a favoritos' if es_favorito else 'Removido de favoritos'
        })

    except Exception as e:
        logger.error(f"Error toggle favorito: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error al actualizar favorito'
        })