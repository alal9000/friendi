from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from app.models import Profile
from .models import Event, EventComment, EventRequest
from app.decorators import check_profile_id
from app.forms import EventForm
from notifications.models import Notification
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.shortcuts import redirect


@login_required
def create(request):
    # Check email verification status
    email_address = EmailAddress.objects.filter(
        user=request.user, email=request.user.email
    ).first()

    if not email_address or not email_address.verified:
        send_email_confirmation(request, request.user)
        messages.warning(
            request,
            "Your email is not verified. A new verification link has been sent to your email address."
            "Please verify your email to create an event.",
        )
        return redirect("home")

    current_user_profile = request.user.profile
    form = EventForm()

    # create event form
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            # Hosting limit check
            if current_user_profile.active_hosted_events_count() >= 3:
                messages.error(request, "You can only host up to 3 upcoming events.")
                return redirect("home")

            new_event = form.save(commit=False)
            if current_user_profile:
                new_event.event_title = " ".join(
                    word.capitalize() for word in new_event.event_title.split()
                )
                new_event.host = current_user_profile
                new_event.save()
                messages.success(request, "Event created successfully.")

                return HttpResponseRedirect(reverse("home"))
            else:
                messages.error(request, "Error creating event. User profile not found.")

    return render(request, "events/create.html", {"form": form})


def event(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    # Check if the event is canceled
    if event.cancelled:
        return render(request, "events/event_cancelled.html")

    # Check if the event is expired
    if event.expired:
        return render(request, "events/event_expired.html")

    request_profile = None
    if request.user.is_authenticated:
        request_profile = request.user.profile

    is_guest = request_profile in event.guests.all()
    is_host = event.host == request_profile

    # calcuate how many currently registered attendees
    total_current_attendees = event.guests.count() + 1

    button = None
    if EventRequest.objects.filter(
        sender=request_profile, host=event.host, event=event
    ).exists():
        button = EventRequest.objects.filter(event_id=event.id).last().status

    if request.method == "POST":
        data = request.POST
        # cancel event
        if "host-cancel" in data:
            if is_host:
                event.cancelled = True
                event.save()

                attendees = [event.host] + list(event.guests.all())
                event_title = event.event_title

                # Notify all attendees
                for attendee in attendees:
                    Notification.objects.create(
                        user=attendee,
                        message=f'The event "{event_title}" has been cancelled.',
                        link=reverse("event", kwargs={"event_id": event.id}),
                    )

                # Notify all attendees via email
                subject = f"Event Cancelled: {event_title}"
                message = f'The event "{event_title}" you were invited to has been cancelled by the host.'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [
                    attendee.user.email
                    for attendee in attendees
                    if attendee.user.email and attendee.email_notifications_enabled
                ]

                send_mail(
                    subject,
                    message,
                    from_email,
                    recipient_list,
                    fail_silently=False,
                )

                # Notify opted-in attendees via SMS
                try:
                    client = Client(
                        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                    )

                    for attendee in attendees:
                        if (
                            attendee.phone_notifications_enabled
                            and attendee.phone_number
                        ):
                            sms_message = f'The event "{event_title}" has been cancelled by the host.'
                            client.messages.create(
                                to=attendee.phone_number,
                                from_=settings.TWILIO_FROM_NUMBER,
                                body=sms_message,
                            )

                except TwilioException as e:
                    print(f"Twilio error during cancellation SMS: {str(e)}")

                messages.success(request, "Event cancelled successfully.")
                return redirect("home")

        # comment
        if is_guest or is_host:
            comment_text = request.POST.get("comment_text")
            EventComment.objects.create(
                profile=request_profile, event=event, comment=comment_text
            )
            messages.success(request, "Your message has been posted successfully.")

            # notify attendees when a comment is added
            attendees = [event.host] + list(event.guests.all())
            for attendee in attendees:
                if attendee != request_profile:
                    Notification.objects.create(
                        user=attendee,
                        message=f"{request_profile} commented in {event.event_title}",
                        link=reverse("event", kwargs={"event_id": event.pk}),
                    )

            # Notify all attendees via email
            commenter_name = str(request_profile)
            subject = f'New comment on "{event.event_title}"'
            message = (
                f'{commenter_name} commented on the event "{event.event_title}".\n\n'
                f'Comment: "{comment_text}"\n\n'
                f'View the event: {request.build_absolute_uri(reverse("event", kwargs={"event_id": event.pk}))}'
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [
                attendee.user.email
                for attendee in attendees
                if (
                    attendee != request_profile
                    and attendee.user.email
                    and attendee.email_notifications_enabled
                )
            ]

            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )

            # Notify all attendees via SMS if opted in
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                for attendee in attendees:
                    if (
                        attendee != request_profile
                        and attendee.phone_notifications_enabled
                        and attendee.phone_number
                    ):
                        sms_message = (
                            f"From Friendi: {commenter_name} commented on '{event.event_title}':\n"
                            f'"{comment_text}"'
                        )
                        client.messages.create(
                            to=attendee.phone_number,
                            from_=settings.TWILIO_FROM_NUMBER,
                            body=sms_message,
                        )

            except TwilioException as e:
                print(f"Twilio error: {str(e)}")

            return redirect("event", event_id=event_id)

        # Join event request
        if "join-event" in data and not is_host:
            if not request.user.is_authenticated:
                return redirect(reverse("account_login"))

            # Check email verification
            email_address = EmailAddress.objects.filter(
                user=request.user, email=request.user.email
            ).first()

            if not email_address or not email_address.verified:
                # send confirmation email again
                send_email_confirmation(request, request.user)

                messages.warning(
                    request,
                    "Your email is not verified. A verification link has been sent to your email address. Please verify your email to join events.",
                )
                return redirect("home")

            # Limit user to only attend up to 3 future events
            if request_profile.active_attending_events_count() >= 3:
                messages.error(
                    request, "You can only attend up to 3 upcoming events at a time."
                )
                return redirect("home")

            # create the join request
            EventRequest.objects.create(
                sender=request_profile, event=event, host=event.host
            )

            Notification.objects.create(
                user=event.host,
                message=f"{request.user.first_name} has requested to join your event",
                link=reverse("event_requests", kwargs={"profile_id": event.host.id}),
            )

            messages.success(request, "Your request to join the event has been sent.")

            # Check if the event should be locked
            total_current_attendees = event.guests.count() + 1
            if total_current_attendees >= event.total_attendees - 1:
                event.locked = True
                event.save()

            button = "pending"

            return redirect("event", event_id=event_id)

    comments = EventComment.objects.filter(event=event)

    context = {
        "event": event,
        "is_guest": is_guest,
        "comments": comments,
        "is_host": is_host,
        "total_current_attendees": total_current_attendees,
        "button": button,
        "locked": event.locked,
    }

    return render(request, "events/event.html", context)


@login_required
def remove_attendee(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    request_profile = request.user.profile

    if request_profile in event.guests.all():
        event.guests.remove(request_profile)
        messages.success(request, "Successfully removed from the event.")

        total_current_attendees = event.guests.count() + 1
        if event.locked and total_current_attendees < event.total_attendees:
            event.locked = False
            event.save()
    else:
        messages.error(request, "You are not currently attending this event.")

    return redirect("home")


@login_required
@check_profile_id
def event_requests(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    host_requests = EventRequest.objects.filter(host=profile, status="pending")
    attendee_requests = EventRequest.objects.filter(sender=profile, status="pending")

    if request.method == "POST":
        # extract data from the form submission
        event_id = request.POST.get("event_id")
        sender_id = request.POST.get("sender_id")
        action = request.POST.get("action")

        # Fetch the Event and EventRequest instance
        event = get_object_or_404(Event, id=event_id)
        event_request = EventRequest.objects.filter(
            host=profile, sender=sender_id, event=event
        ).last()

        if action == "approve":
            event_request.status = "accepted"
            event.guests.add(event_request.sender)
            event_request.save()

            Notification.objects.create(
                user=event_request.sender,
                message=f"Your request to join {event.event_title} has been approved",
                link=reverse("event", kwargs={"event_id": event.id}),
            )
            messages.success(request, "Event request approved.")

        elif action == "deny":
            event_request.status = "denied"
            event_request.save()

            # Check if the event is currently locked and needs to be unlocked
            total_current_attendees = event.guests.count() + 1
            if event.locked and total_current_attendees < event.total_attendees:
                event.locked = False
                event.save()

            Notification.objects.create(
                user=event_request.sender,
                message=f"Your request to join {event.event_title} has not been approved",
                link=reverse("event", kwargs={"event_id": event.id}),
            )
            messages.success(request, "Event request not approved.")

        return redirect("event", event_id=event.id)

    context = {
        "host_requests": host_requests,
        "attendee_requests": attendee_requests,
    }

    return render(request, "events/event_requests.html", context)
