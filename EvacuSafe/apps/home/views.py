from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import EvacuationCenterCreateForm
from .models import EvacuationCenter


def _serialize_center(center):
    return {
        'id': center.pk,
        'name': center.name,
        'location': center.location,
        'status': center.get_status_display(),
        'status_key': center.status,
        'occupants': center.occupants,
        'capacity': center.capacity,
        'coordinates_are_approximate': center.coordinates_are_approximate,
        'latitude': float(center.latitude) if center.latitude is not None else None,
        'longitude': float(center.longitude) if center.longitude is not None else None,
    }


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
        'standby_count': centers.filter(status='standby').count(),
        'closed_count': centers.filter(status='closed').count(),
        'total_count': total_count,
        'total_occupants': totals['total_occupants'] or 0,
        'total_capacity': totals['total_capacity'] or 0,
        'map_centers': [
            _serialize_center(center)
            for center in centers
            if center.latitude is not None and center.longitude is not None
        ],
        'centers_data': [_serialize_center(center) for center in centers],
        'unmapped_center_count': sum(
            1
            for center in centers
            if center.latitude is None or center.longitude is None
        ),
        'approximate_center_count': sum(
            1
            for center in centers
            if center.latitude is not None
            and center.longitude is not None
            and center.coordinates_are_approximate
        ),
    }
    return render(request, 'home/home.html', context)


@login_required
@require_POST
def manage_center_view(request):
    form = EvacuationCenterCreateForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    center = form.save()
    centers = EvacuationCenter.objects.all()
    totals = centers.aggregate(
        total_capacity=Sum('capacity'),
        total_occupants=Sum('occupants'),
    )
    return JsonResponse({
        'center': _serialize_center(center),
        'summary': {
            'active_count': centers.filter(status='active').count(),
            'standby_count': centers.filter(status='standby').count(),
            'closed_count': centers.filter(status='closed').count(),
            'total_count': centers.count(),
            'total_occupants': totals['total_occupants'] or 0,
            'total_capacity': totals['total_capacity'] or 0,
        },
        'unmapped_center_count': centers.filter(
            latitude__isnull=True,
        ).count() + centers.filter(
            longitude__isnull=True,
            latitude__isnull=False,
        ).count(),
        'approximate_center_count': centers.filter(
            coordinates_are_approximate=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).count(),
        'message': f'{center.name} was added.',
    })
