from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from app.models import Event


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
