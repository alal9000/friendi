from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from events.models import Event
from twilio.rest import Client
from twilio.base.exceptions import TwilioException


def send_event_reminders():
    print("send_event_reminders ran")
    now = timezone.now()
    tomorrow = now + timedelta(days=1)

    # Get tomorrow's date range
    tomorrow_start = datetime.combine(tomorrow.date(), datetime.min.time())
    tomorrow_end = datetime.combine(tomorrow.date(), datetime.max.time())
    tomorrow_start = timezone.make_aware(tomorrow_start)
    tomorrow_end = timezone.make_aware(tomorrow_end)

    # Find all events happening tomorrow that are not cancelled and are locked
    events = Event.objects.filter(
        cancelled=False,
        locked=True,
        event_date=tomorrow.date(),
    )

    for event in events:
        # Re-implement the "expired" logic in Python
        event_datetime = datetime.combine(event.event_date, event.event_time)
        event_datetime = timezone.make_aware(
            event_datetime, timezone.get_current_timezone()
        )

        if timezone.now() > (event_datetime + timedelta(hours=1)):
            continue  # skip expired

        # email reminders
        attendees = list(event.guests.all())
        if event.host:
            attendees.append(event.host)

        emails = [
            p.user.email
            for p in attendees
            if p.user and p.user.email and p.email_notifications_enabled
        ]

        if not emails:
            continue

        subject = f"Reminder: '{event.event_title}' is happening tomorrow!"
        message = f"""
            Hi there,

            This is a Friendi reminder that the event "{event.event_title}" is scheduled for:

            📅 Date: {event.event_date}
            🕒 Time: {event.event_time.strftime('%I:%M %p')}
            📍 Location: {event.location or 'No location provided'}

            Description:
            {event.description}

            See your event here: https://friendi.com.au/events/event/{event.id}

            See you there!

            Thanks, 
            Friendi Team
            """

        for email in emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],  # single recipient only
                fail_silently=False,
            )

        # SMS reminders
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

            for attendee in attendees:
                if attendee.phone_notifications_enabled and attendee.phone_number:
                    sms_message = f"Friendi Reminder: '{event.event_title}' is tomorrow at {event.event_time.strftime('%I:%M %p')}. See your event here: https://friendi.com.au/events/event/{event.id}"
                    client.messages.create(
                        to=attendee.phone_number,
                        from_=settings.TWILIO_FROM_NUMBER,
                        body=sms_message,
                    )

        except TwilioException as e:
            print(f"Twilio error during reminder SMS: {str(e)}")


def cleanup_old_events():
    print("cleanup_old_events ran")
    # Bulk delete cancelled events
    cancelled_count, _ = Event.objects.filter(cancelled=True).delete()

    # Collect expired event IDs to bulk delete
    expired_event_ids = [event.id for event in Event.objects.all() if event.expired]
    expired_count, _ = Event.objects.filter(id__in=expired_event_ids).delete()

    return {"cancelled_deleted": cancelled_count, "expired_deleted": expired_count}


def test_print():
    print("Django-Q scheduler test: task executed!")
