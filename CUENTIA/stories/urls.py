#stories/urls.py
from django.urls import path
from . import views

app_name = 'stories'

urlpatterns = [
    # Generar cuento
    path('generar/', views.generar_cuento_view, name='generar'),
    path('generando/', views.generando_cuento_view, name='generando'),

    # Ver cuento
    path('cuento/<int:cuento_id>/', views.generated_story_view, name='generated_story'),
    path('cuento/<int:cuento_id>/status/', views.check_cuento_status, name='check_cuento_status'),

    # Acciones del cuento
    path('cuento/<int:cuento_id>/pdf/', views.descargar_pdf_view, name='descargar_pdf'),
    path('cuento/<int:cuento_id>/guardar/', views.guardar_biblioteca_view, name='guardar_biblioteca'),
    path('cuento/<int:cuento_id>/favorito/', views.toggle_favorito_view, name='toggle_favorito'),

    # Lista de cuentos
    path('lista/', views.lista_cuentos_view, name='lista_cuentos'),

    # Traducción (opcional - comentado por ahora)
    # path('cuento/<int:cuento_id>/translate/', views.translate_story_ajax, name='translate_story'),
]

