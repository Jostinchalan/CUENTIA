# library/urls.py
from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    # Cambiar 'index' por 'biblioteca' para que coincida con tu template
    path('', views.biblioteca_view, name='index'),  # Mantener 'index' como nombre pero apuntar a biblioteca_view
    path('seguimiento/', views.seguimiento_view, name='seguimiento'),
    path('generar/', views.generar_view, name='generar'),
]