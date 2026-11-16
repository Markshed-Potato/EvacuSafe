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
        'map_centers': [
            {
                'name': center.name,
                'location': center.location,
                'status': center.get_status_display(),
                'status_key': center.status,
                'occupants': center.occupants,
                'capacity': center.capacity,
                'latitude': float(center.latitude),
                'longitude': float(center.longitude),
            }
            for center in centers
            if center.latitude is not None and center.longitude is not None
        ],
        'unmapped_center_count': sum(
            1
            for center in centers
            if center.latitude is None or center.longitude is None
        ),
    }
    return render(request, 'home/home.html', context)
