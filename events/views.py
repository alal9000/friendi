from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from app.models import Profile
from .models import Event, Comment, EventRequest
from app.decorators import check_profile_id
from app.forms import EventForm
from notifications.models import Notification


@login_required
def create(request):
    current_user_profile = request.user.profile
    form = EventForm()

    # create event form
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
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
                messages.success(request, "Event cancelled successfully.")
                return redirect("home")

        # comment
        if is_guest or is_host:
            comment_text = request.POST.get("comment_text")
            Comment.objects.create(
                profile=request_profile, event=event, comment=comment_text
            )

            # notify attendees when a comment is added
            attendees = [event.host] + list(event.guests.all())
            for attendee in attendees:
                if attendee != request_profile:
                    Notification.objects.create(
                        user=attendee,
                        message=f"{request_profile} commented in {event.event_title}",
                        link=reverse("event", kwargs={"event_id": event.pk}),
                    )

            return redirect("event", event_id=event_id)

        # Join event request
        if "join-event" in data and not is_host:
            if not request.user.is_authenticated:
                return redirect(reverse("account_login"))
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
            if total_current_attendees == event.total_attendees - 1:
                event.locked = True
                event.save()

            button = "pending"

            return redirect("event", event_id=event_id)

    comments = Comment.objects.filter(event=event)

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
