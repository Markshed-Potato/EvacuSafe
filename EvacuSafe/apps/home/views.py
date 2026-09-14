from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from .models import EvacuationCenter


@login_required
def home_view(request):
    centers = EvacuationCenter.objects.all()
    totals = centers.aggregate(
        total_capacity=Sum('capacity'),
        total_occupants=Sum('occupants'),
    )
    active_count = centers.filter(status='active').count()
    total_count = centers.count()

    context = {
        'centers': centers,
        'active_count': active_count,
        'total_count': total_count,
        'total_occupants': totals['total_occupants'] or 0,
        'total_capacity': totals['total_capacity'] or 0,
    }
    return render(request, 'home/home.html', context)
