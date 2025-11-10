from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from events.models import Event
from twilio.rest import Client
import logging
from twilio.base.exceptions import TwilioException
from django.db.models import Count, F, IntegerField, Value, ExpressionWrapper


def send_event_reminders():
    logger = logging.getLogger(__name__)
    logger.info("send_event_reminders ran")
    today = timezone.localdate()
    logger.info(f"today (AEST): {today}")

    # Find all events happening today that are full
    events = (
        Event.objects.filter(
            cancelled=False,
            event_date=today,
            total_attendees__isnull=False,
            host__isnull=False,
        )
        .annotate(
            guest_count=Count("guests", distinct=True),
            attendee_count=ExpressionWrapper(
                Count("guests", distinct=True) + Value(1), output_field=IntegerField()
            ),
        )
        .filter(attendee_count=F("total_attendees"))
    )

    logger.info(f"Found {events.count()} full events for today:")

    for event in events:
        logger.info(
            f"Checking event: {event.event_title} ({event.event_date} at {event.event_time})"
        )

        # Re-implement the "expired" logic in Python
        event_datetime = datetime.combine(event.event_date, event.event_time)
        event_datetime = timezone.make_aware(
            event_datetime, timezone.get_current_timezone()
        )

        if timezone.now() > event_datetime:
            logger.info(f"Skipping expired event: {event.event_title}")
            continue

        # Email reminders
        attendees = list(event.guests.all())
        if event.host:
            attendees.append(event.host)

        logger.info(f"Number of attendees: {len(attendees)}")

        logger.info(f"Reminders sent for event: {event.event_title}")

        emails = [
            p.user.email
            for p in attendees
            if p.user and p.user.email and p.email_notifications_enabled
        ]

        logger.info(f"Emails found: {emails}")

        if not emails:
            logger.info(f"No email-enabled attendees for event: {event.event_title}")
            continue

        subject = f"A Friendi Reminder: '{event.event_title}' is happening soon!"
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
                    sms_message = f"From Friendi: This is a Friendi Reminder, '{event.event_title}' is happening soon at {event.event_time.strftime('%I:%M %p')}. See your event here: https://friendi.com.au/events/event/{event.id}"
                    client.messages.create(
                        to=attendee.phone_number,
                        from_=settings.TWILIO_FROM_NUMBER,
                        body=sms_message,
                    )
        except TwilioException as e:
            logger.exception("Twilio error during reminder SMS")

        logger.info(f"Reminders sent for event: {event.event_title}")


def cleanup_old_events():
    logger = logging.getLogger(__name__)
    logger.info("cleanup_old_events ran")
    # Bulk delete cancelled events
    cancelled_count, _ = Event.objects.filter(cancelled=True).delete()

    # Collect expired event IDs to bulk delete
    expired_event_ids = [event.id for event in Event.objects.all() if event.expired]
    expired_count, _ = Event.objects.filter(id__in=expired_event_ids).delete()

    return {"cancelled_deleted": cancelled_count, "expired_deleted": expired_count}


def test_print():
    print("Django-Q scheduler test: task executed!")
