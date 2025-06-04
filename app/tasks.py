import logging
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from events.models import Event


def send_event_reminders():
    now = timezone.now()
    tomorrow = now + timedelta(days=1)

    events = Event.objects.filter(
        cancelled=False, locked=False, event_date=tomorrow.date()
    )

    for event in events:
        # Get all attendee email addresses
        attendees = list(event.guests.all())
        if event.host:
            attendees.append(event.host)

        emails = [p.user.email for p in attendees if p.user and p.user.email]

        if not emails:
            continue

        subject = f"Reminder: '{event.event_title}' is happening tomorrow!"
        message = f"""
Hi there,

This is a friendly reminder that the event "{event.event_title}" is scheduled for:

📅 Date: {event.event_date}
🕒 Time: {event.event_time.strftime('%I:%M %p')}
📍 Location: {event.location or 'No location provided'}

Description:
{event.description}

See you there!

- Your Events App
"""

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=False,
        )


def cleanup_old_events():
    logger = logging.getLogger(__name__)
    now = timezone.now()
    logger.info("Running cleanup task...")

    # Bulk delete cancelled events
    cancelled_count, _ = Event.objects.filter(cancelled=True).delete()

    # Collect expired event IDs to bulk delete
    expired_event_ids = [event.id for event in Event.objects.all() if event.expired]
    expired_count, _ = Event.objects.filter(id__in=expired_event_ids).delete()

    logger.info(
        f"Deleted {cancelled_count} cancelled events and {expired_count} expired events."
    )
    return {"cancelled_deleted": cancelled_count, "expired_deleted": expired_count}
