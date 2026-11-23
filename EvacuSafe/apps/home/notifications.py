from django.conf import settings
from django.core.mail import send_mail
from apps.user_settings.models import UserSettings


def get_subscribed_emails():
    """Returns list of active user emails who have opted into email notifications."""
    try:
        subscribers = UserSettings.objects.filter(
            email_notifications=True,
            user__is_active=True,
        ).select_related('user')
        emails = [s.user.email.strip() for s in subscribers if s.user.email and '@' in s.user.email]
        return list(set(emails))
    except Exception:
        return []


def notify_capacity_limit(center):
    """Sends email alert when evacuation center hits 100% capacity or exceeds 85%."""
    recipients = get_subscribed_emails()
    if not recipients:
        return 0

    if center.is_full:
        subject = f"[CRITICAL ALERT] Evacuation Center at Maximum Capacity: {center.name}"
        message = (
            f"URGENT DISASTER RESPONSE ALERT\n\n"
            f"Evacuation Center: {center.name}\n"
            f"Location: {center.location or 'Not specified'}\n"
            f"Current Occupancy: {center.occupants} / {center.capacity} (100% FULL)\n"
            f"Status: {center.get_status_display()}\n\n"
            f"Action Required: Immediately redirect incoming evacuees to alternative standby or active centers.\n\n"
            f"-- EvacuSafe Automated Alert System"
        )
    elif center.is_near_capacity:
        subject = f"[WARNING] Evacuation Center Near Capacity ({center.occupancy_rate}%): {center.name}"
        message = (
            f"DISASTER RESPONSE WARNING\n\n"
            f"Evacuation Center: {center.name}\n"
            f"Location: {center.location or 'Not specified'}\n"
            f"Current Occupancy: {center.occupants} / {center.capacity} ({center.occupancy_rate}%)\n\n"
            f"Action Required: Prepare secondary facilities in this sector.\n\n"
            f"-- EvacuSafe Automated Alert System"
        )
    else:
        return 0

    try:
        return send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@evacusafe.org'),
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        return 0


def notify_new_incident(incident):
    """Sends email alert when a high or critical severity incident is declared."""
    if incident.severity not in ('high', 'critical'):
        return 0

    recipients = get_subscribed_emails()
    if not recipients:
        return 0

    subject = f"[EMERGENCY ALERT] {incident.get_severity_display().upper()} Incident Declared: {incident.title}"
    message = (
        f"DISASTER INCIDENT BROADCAST\n\n"
        f"Incident: {incident.title}\n"
        f"Type: {incident.get_disaster_type_display()}\n"
        f"Severity: {incident.get_severity_display().upper()}\n"
        f"Location: {incident.location or 'General Sector'}\n"
        f"Description: {incident.description or 'No operational notes provided.'}\n"
        f"Declared At: {incident.declared_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"All assigned response teams and coordinators should report to command status.\n\n"
        f"-- EvacuSafe Incident Command"
    )

    try:
        return send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@evacusafe.org'),
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        return 0
