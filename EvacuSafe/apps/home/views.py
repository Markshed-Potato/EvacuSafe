from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    EvacuationCenterCreateForm,
    EvacuationCenterUpdateForm,
    IncidentForm,
    ResourceInventoryForm,
)
from .models import AuditLog, EvacuationCenter, Incident, ResourceInventory
from .notifications import notify_capacity_limit, notify_new_incident
from .permissions import (
    admin_required,
    coordinator_required,
    get_user_role,
    is_admin,
    is_coordinator_or_admin,
)


def _serialize_resource(center):
    try:
        res = getattr(center, 'resources', None)
        if not res:
            res, _ = ResourceInventory.objects.get_or_create(center=center)
        return {
            'food_packs': res.food_packs,
            'water_liters': res.water_liters,
            'medical_kits': res.medical_kits,
            'blankets': res.blankets,
            'updated_at': res.updated_at.strftime('%Y-%m-%d %H:%M') if res.updated_at else '',
        }
    except Exception:
        return {'food_packs': 0, 'water_liters': 0, 'medical_kits': 0, 'blankets': 0, 'updated_at': ''}


def _serialize_center(center):
    return {
        'id': center.pk,
        'name': center.name,
        'location': center.location,
        'status': center.get_status_display(),
        'status_key': center.status,
        'occupants': center.occupants,
        'capacity': center.capacity,
        'occupancy_rate': center.occupancy_rate,
        'is_full': center.is_full,
        'is_near_capacity': center.is_near_capacity,
        'is_archived': center.is_archived,
        'coordinates_are_approximate': center.coordinates_are_approximate,
        'latitude': float(center.latitude) if center.latitude is not None else None,
        'longitude': float(center.longitude) if center.longitude is not None else None,
        'resources': _serialize_resource(center),
    }


def _center_summary(centers):
    totals = centers.aggregate(
        total_capacity=Sum('capacity'),
        total_occupants=Sum('occupants'),
    )
    return {
        'active_count': centers.filter(status='active').count(),
        'standby_count': centers.filter(status='standby').count(),
        'closed_count': centers.filter(status='closed').count(),
        'total_count': centers.count(),
        'total_occupants': totals['total_occupants'] or 0,
        'total_capacity': totals['total_capacity'] or 0,
    }


def _center_location_counts(centers):
    return {
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
    }


@login_required
def home_view(request):
    # Non-archived centers for primary dashboard
    centers = EvacuationCenter.objects.filter(is_archived=False)
    totals = centers.aggregate(
        total_capacity=Sum('capacity'),
        total_occupants=Sum('occupants'),
    )
    active_count = centers.filter(status='active').count()
    standby_count = centers.filter(status='standby').count()
    closed_count = centers.filter(status='closed').count()
    total_count = centers.count()

    # User role context
    user_role = get_user_role(request.user)
    can_coordinate = is_coordinator_or_admin(request.user)
    can_admin = is_admin(request.user)

    # Activity Audit Logs & Active Incidents
    recent_logs = AuditLog.objects.select_related('user')[:15]
    active_incidents = Incident.objects.filter(is_active=True).select_related('declared_by')[:10]
    archived_centers = EvacuationCenter.objects.filter(is_archived=True)

    context = {
        'centers': centers,
        'archived_centers': archived_centers,
        'archived_count': archived_centers.count(),
        'status_choices': EvacuationCenter.STATUS_CHOICES,
        'active_count': active_count,
        'standby_count': standby_count,
        'closed_count': closed_count,
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
        'user_role': user_role,
        'is_coordinator': can_coordinate,
        'is_admin': can_admin,
        'recent_logs': recent_logs,
        'active_incidents': active_incidents,
        'incident_form': IncidentForm(),
    }
    return render(request, 'home/home.html', context)


@login_required
@require_POST
@coordinator_required
def manage_center_view(request):
    form = EvacuationCenterCreateForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    center = form.save()
    ResourceInventory.objects.get_or_create(center=center)

    # Audit Logging
    AuditLog.objects.create(
        center=center,
        center_name=center.name,
        user=request.user,
        action='create',
        new_status=center.status,
        new_occupants=center.occupants,
        new_capacity=center.capacity,
        details=f"Center created with initial capacity {center.capacity} and {center.occupants} occupants."
    )

    # Automated Email Alert if critical
    notify_capacity_limit(center)

    centers = EvacuationCenter.objects.filter(is_archived=False)
    return JsonResponse({
        'center': _serialize_center(center),
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'message': f'{center.name} was added.',
    })


@login_required
@require_POST
@coordinator_required
def update_center_view(request, center_id):
    center = get_object_or_404(EvacuationCenter, pk=center_id)
    old_status = center.status
    old_occupants = center.occupants
    old_capacity = center.capacity

    form = EvacuationCenterUpdateForm(request.POST, instance=center)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    center = form.save()

    # Audit Logging
    AuditLog.objects.create(
        center=center,
        center_name=center.name,
        user=request.user,
        action='update',
        old_status=old_status,
        new_status=center.status,
        old_occupants=old_occupants,
        new_occupants=center.occupants,
        old_capacity=old_capacity,
        new_capacity=center.capacity,
        details=f"Updated status ({old_status} -> {center.status}) and occupants ({old_occupants} -> {center.occupants})."
    )

    # Automated Email Alert if capacity changed to critical
    notify_capacity_limit(center)

    centers = EvacuationCenter.objects.filter(is_archived=False)
    return JsonResponse({
        'center': _serialize_center(center),
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'message': f'{center.name} was updated.',
    })


@login_required
@require_POST
@coordinator_required
def archive_center_view(request, center_id):
    center = get_object_or_404(EvacuationCenter, pk=center_id)
    old_status = center.status
    center.is_archived = True
    center.archived_at = timezone.now()
    center.archived_by = request.user
    center.status = 'closed'
    center.save()

    AuditLog.objects.create(
        center=center,
        center_name=center.name,
        user=request.user,
        action='archive',
        old_status=old_status,
        new_status='closed',
        old_occupants=center.occupants,
        new_occupants=center.occupants,
        details=f"Center archived and soft-deleted by {request.user.username}."
    )

    centers = EvacuationCenter.objects.filter(is_archived=False)
    return JsonResponse({
        'center': _serialize_center(center),
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'message': f'{center.name} has been archived.',
    })


@login_required
@require_POST
@coordinator_required
def restore_center_view(request, center_id):
    center = get_object_or_404(EvacuationCenter, pk=center_id)
    center.is_archived = False
    center.archived_at = None
    center.archived_by = None
    center.status = 'standby'
    center.save()

    AuditLog.objects.create(
        center=center,
        center_name=center.name,
        user=request.user,
        action='restore',
        new_status='standby',
        details=f"Center restored to active registry by {request.user.username}."
    )

    centers = EvacuationCenter.objects.filter(is_archived=False)
    return JsonResponse({
        'center': _serialize_center(center),
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'message': f'{center.name} has been restored.',
    })


@login_required
@require_POST
@admin_required
def delete_center_view(request, center_id):
    center = get_object_or_404(EvacuationCenter, pk=center_id)
    center_name = center.name

    AuditLog.objects.create(
        center_name=center_name,
        user=request.user,
        action='delete',
        old_status=center.status,
        old_occupants=center.occupants,
        old_capacity=center.capacity,
        details=f"Center permanently deleted by Admin {request.user.username}."
    )

    center.delete()

    centers = EvacuationCenter.objects.filter(is_archived=False)
    return JsonResponse({
        'deleted_id': center_id,
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'message': f'{center_name} was permanently deleted.',
    })


@login_required
def live_centers_api(request):
    """
    Lightweight JSON endpoint polling status every 10-15s.
    Returns live center markers, stats, active incidents, and audit feed.
    """
    centers = EvacuationCenter.objects.filter(is_archived=False)
    recent_logs = AuditLog.objects.select_related('user')[:10]
    active_incidents = Incident.objects.filter(is_active=True).select_related('declared_by')[:5]

    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().strftime('%H:%M:%S'),
        'summary': _center_summary(centers),
        **_center_location_counts(centers),
        'centers': [_serialize_center(c) for c in centers],
        'audit_logs': [
            {
                'id': log.id,
                'action': log.get_action_display(),
                'action_key': log.action,
                'center_name': log.center_name,
                'user': log.user.username if log.user else 'System',
                'details': log.details,
                'timestamp': log.timestamp.strftime('%H:%M:%S'),
            }
            for log in recent_logs
        ],
        'active_incidents': [
            {
                'id': inc.id,
                'title': inc.title,
                'type': inc.get_disaster_type_display(),
                'severity': inc.severity,
                'location': inc.location,
                'declared_at': inc.declared_at.strftime('%b %d, %H:%M'),
            }
            for inc in active_incidents
        ],
    })


@login_required
@require_POST
@coordinator_required
def declare_incident_view(request):
    form = IncidentForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    incident = form.save(commit=False)
    incident.declared_by = request.user
    incident.save()

    AuditLog.objects.create(
        center_name=incident.title,
        user=request.user,
        action='create',
        details=f"Incident declared: {incident.title} ({incident.get_severity_display()} severity) in {incident.location or 'unspecified area'}."
    )

    notify_new_incident(incident)

    return JsonResponse({
        'incident': {
            'id': incident.id,
            'title': incident.title,
            'type': incident.get_disaster_type_display(),
            'severity': incident.severity,
            'location': incident.location,
            'description': incident.description,
            'declared_at': incident.declared_at.strftime('%b %d, %H:%M'),
        },
        'message': f"Emergency Incident '{incident.title}' declared.",
    })


@login_required
@require_POST
@coordinator_required
def resolve_incident_view(request, incident_id):
    incident = get_object_or_404(Incident, pk=incident_id)
    incident.is_active = False
    incident.resolved_at = timezone.now()
    incident.save()

    AuditLog.objects.create(
        center_name=incident.title,
        user=request.user,
        action='update',
        details=f"Incident '{incident.title}' marked as resolved by {request.user.username}."
    )

    return JsonResponse({
        'id': incident.id,
        'message': f"Incident '{incident.title}' marked as resolved.",
    })


@login_required
@require_POST
@coordinator_required
def update_resource_view(request, center_id):
    center = get_object_or_404(EvacuationCenter, pk=center_id)
    resource, _ = ResourceInventory.objects.get_or_create(center=center)

    form = ResourceInventoryForm(request.POST, instance=resource)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    resource = form.save(commit=False)
    resource.updated_by = request.user
    resource.save()

    AuditLog.objects.create(
        center=center,
        center_name=center.name,
        user=request.user,
        action='update',
        details=f"Updated supplies: {resource.food_packs} food, {resource.water_liters}L water, {resource.medical_kits} med kits, {resource.blankets} blankets."
    )

    return JsonResponse({
        'center_id': center.id,
        'resources': _serialize_resource(center),
        'message': f"Resource inventory updated for {center.name}.",
    })
