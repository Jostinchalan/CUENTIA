from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stories.models import Cuento, EstadisticaLectura
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_view(request):
    """Vista principal del dashboard"""

    # Estadísticas del usuario
    total_cuentos = Cuento.objects.filter(
        usuario=request.user,
        estado='completado'
    ).count()

    # Cuentos este mes
    inicio_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    cuentos_este_mes = Cuento.objects.filter(
        usuario=request.user,
        estado='completado',
        fecha_creacion__gte=inicio_mes
    ).count()

    # Tiempo total de lectura
    tiempo_total = EstadisticaLectura.objects.filter(
        usuario=request.user
    ).aggregate(
        total=Sum('tiempo_lectura')
    )['total'] or 0

    # Tema favorito
    tema_favorito = Cuento.objects.filter(
        usuario=request.user,
        estado='completado'
    ).values('tema').annotate(
        count=Count('tema')
    ).order_by('-count').first()

    # Cuentos recientes (actividad reciente)
    cuentos_recientes = Cuento.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:3]

    # Cuentos más leídos (populares)
    cuentos_populares = Cuento.objects.filter(
        usuario=request.user,
        estado='completado'
    ).order_by('-veces_leido')[:3]

    # Calcular horas y minutos
    horas = (tiempo_total // 3600) if tiempo_total else 0
    minutos = ((tiempo_total % 3600) // 60) if tiempo_total else 0

    context = {
        'user': request.user,
        'total_cuentos': total_cuentos,
        'cuentos_este_mes': cuentos_este_mes,
        'tiempo_total_horas': horas,
        'tiempo_total_minutos': minutos,
        'tema_favorito': tema_favorito['tema'].upper() if tema_favorito else 'AVENTURA',
        'cuentos_recientes': cuentos_recientes,
        'cuentos_populares': cuentos_populares,
    }

    return render(request, 'dashboard.html', context)
