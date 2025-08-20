from datetime import timedelta
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.messages import get_messages
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

from app.models import Profile, StatusUpdate
from events.models import Event
from friends.models import Friend
from app.decorators import check_profile_id
from notifications.models import Notification
from photos.models import Photo
from app.forms import (
    ProfileUpdateForm,
    StatusUpdateForm,
    UserUpdateForm,
    ProfileDescriptionForm,
    InviteFriendForm,
)


def profile(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    current_user_profile = None

    is_first_visit = False
    if request.user.is_authenticated and request.user.profile == profile:
        user_profile = request.user.profile
        if not user_profile.has_seen_tour:
            is_first_visit = True
            user_profile.has_seen_tour = True
            user_profile.save()

    if request.GET.get("image_updated") == "true":
        messages.success(request, "Your profile image has been successfully updated.")

    # Check if it's the first visit after login to send support message
    if (
        request.user.is_authenticated
        and request.user.profile == profile
        and "profile_support_message_shown" not in request.session
    ):
        messages.success(
            request,
            "Your support helps keep us going. Tell your friends and family about Friendi or invite them below.",
        )
        # Set the session flag to indicate that the message has been shown
        request.session["profile_support_message_shown"] = True

    if request.user.is_authenticated:
        current_user_profile = request.user.profile

    # Check if the page requestor is in the current profile's friend list
    is_friend = False
    if (
        Friend.objects.filter(
            sender=current_user_profile, receiver=profile, status="accepted"
        ).exists()
        or Friend.objects.filter(
            sender=profile, receiver=current_user_profile, status="accepted"
        ).exists()
    ):
        is_friend = True

    user_photos = Photo.objects.filter(profile=profile).order_by("-timestamp")[:2]
    user_instance = profile.user
    friend_visibility = profile.friend_visibility

    # Determine friendship status
    friend_status = None
    if Friend.objects.filter(sender=current_user_profile, receiver=profile).exists():
        friend_status = Friend.objects.get(
            sender=current_user_profile, receiver=profile
        ).status
    elif Friend.objects.filter(sender=profile, receiver=current_user_profile).exists():
        friend_status = Friend.objects.get(
            sender=profile, receiver=current_user_profile
        ).status

    if friend_status == "pending":
        button = "Pending"
    elif friend_status == "accepted":
        button = "Accepted"
    elif friend_status == "denied":
        button = "Add"
    else:
        button = "Add"

    current_datetime = timezone.now()
    twenty_four_hours_ago = current_datetime - timedelta(hours=24)
    twenty_four_hours_ago_date = twenty_four_hours_ago.date()
    twenty_four_hours_ago_time = twenty_four_hours_ago.time()

    # Filter attended events
    attended_events = Event.objects.filter(
        guests=profile,
        cancelled=False,
        event_date__gte=twenty_four_hours_ago_date,
    ).filter(
        event_date=twenty_four_hours_ago_date,
        event_time__gte=twenty_four_hours_ago_time,
    ) | Event.objects.filter(
        guests=profile,
        cancelled=False,
        event_date__gt=twenty_four_hours_ago_date,
    )

    # Use Python to exclude expired ones
    attended_events = [event for event in attended_events if not event.expired]

    # Filter hosted events
    hosted_events = Event.objects.filter(
        host=profile,
        cancelled=False,
        event_date__gte=twenty_four_hours_ago_date,
    ).filter(
        event_date=twenty_four_hours_ago_date,
        event_time__gte=twenty_four_hours_ago_time,
    ) | Event.objects.filter(
        host=profile,
        cancelled=False,
        event_date__gt=twenty_four_hours_ago_date,
    )

    hosted_events = [event for event in hosted_events if not event.expired]

    # Get friends
    friends_as_sender = Friend.objects.filter(
        sender=profile, status="accepted"
    ).values_list("receiver", flat=True)
    friends_as_receiver = Friend.objects.filter(
        receiver=profile, status="accepted"
    ).values_list("sender", flat=True)
    friend_ids = list(friends_as_sender) + list(friends_as_receiver)
    friends = Profile.objects.filter(id__in=friend_ids)[:4]

    # initalize forms
    user_form = UserUpdateForm(instance=user_instance)
    description_form = ProfileDescriptionForm(instance=profile)
    status_form = StatusUpdateForm(request.POST)
    invite_friend_form = InviteFriendForm()

    # Retrieve the latest status update for the current profile
    latest_status_update = StatusUpdate.objects.filter(
        profile=current_user_profile
    ).first()

    # handle form submissions
    if request.method == "POST":
        # Status update form
        # if "status-update" in request.POST:
        #     status_form = StatusUpdateForm(request.POST, request.FILES)
        #     if status_form.is_valid():
        #         status_update = status_form.save(commit=False)
        #         status_update.profile = current_user_profile

        #         # Save image if uploaded
        #         if "status_image" in request.FILES:
        #             status_update.image = request.FILES["status_image"]

        #         status_update.save()  # Now save to DB
        #         messages.success(request, "Status update posted successfully.")
        #         return redirect("profile", profile_id=profile_id)
        # end Status update form

        # Clear status form
        # if "clear-status" in request.POST:
        #     if latest_status_update:
        #         latest_status_update.delete()
        #         messages.success(request, "Status update cleared successfully.")
        #     return redirect("profile", profile_id=profile_id)
        # End clear status form

        # friend form
        if "friend-button" in request.POST:
            if not request.user.is_authenticated:
                return redirect(reverse("account_login"))
            if request.POST["friend-button"] == "Add":

                # Check if the user's email is verified
                email_address = EmailAddress.objects.filter(
                    user=request.user, email=request.user.email
                ).first()

                if not email_address or not email_address.verified:
                    # resend verification email
                    send_email_confirmation(request, request.user)

                    messages.warning(
                        request,
                        "Your email is not verified. A verification link has been sent to your email address. Please verify your email to send friend requests.",
                    )
                    return redirect("home")

                button = "Pending"
                if not Friend.objects.filter(
                    sender=current_user_profile, receiver=profile, status="pending"
                ).exists():
                    Friend.objects.create(
                        sender=current_user_profile, receiver=profile, status="pending"
                    )
                    Notification.objects.create(
                        user=profile,
                        message="You have a new friend request",
                        link=reverse("friend_requests", args=[profile_id]),
                    )

                    messages.success(request, "Friend request sent successfully.")
                    return redirect(reverse("home"))
        # end friend form

        # description form
        if "update-description" in request.POST:
            description_form = ProfileDescriptionForm(request.POST, instance=profile)
            if description_form.is_valid():
                description_form.save()
                messages.success(request, "About me updated successfully.")
                return redirect("profile", profile_id=profile_id)
        # end description form

        # Invite friend form
        if "invite-friend" in request.POST:
            invite_friend_form = InviteFriendForm(request.POST)
            if invite_friend_form.is_valid():
                email = invite_friend_form.cleaned_data["email"]
                # Send an email invitation
                message = (
                    f"Hi, <a href='https://friendi.com.au/accounts/profile/{request.user.profile.id}'>{request.user.first_name} {request.user.last_name}</a> "
                    "has invited you to join Friendi. Make new friends and attend events in Sydney. Sign up at: <a href='https://friendi.com.au/accounts/signup/'>friendi.com.au/accounts/signup</a>"
                )
                send_mail(
                    "Invitation to Friendi",
                    "",
                    settings.EMAIL_HOST_USER,
                    [email],
                    html_message=message,
                    fail_silently=False,
                )
                messages.success(request, "Invitation sent successfully.")
                return redirect("profile", profile_id=profile_id)
        # end invite friend form
    # end handle form submissions

    storage = get_messages(request)
    success_message = None
    for message in storage:
        if message.tags == "success":
            success_message = message

    context = {
        "is_friend": is_friend,
        "status_form": status_form,
        "invite_friend_form": invite_friend_form,
        "user_form": user_form,
        "user_photos": user_photos,
        "attended_events": attended_events,
        "hosted_events": hosted_events,
        "profile": profile,
        "friends": friends,
        "friend_visibility": friend_visibility,
        "button": button,
        "is_first_visit": is_first_visit,
        "description_form": description_form,
        "success_message": success_message,
        "latest_status_update": latest_status_update,
    }

    return render(request, "app/profile.html", context)


@login_required
@check_profile_id
def profile_settings(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)
    user_instance = profile.user
    user_form = UserUpdateForm(instance=user_instance)
    profile_form = ProfileUpdateForm(instance=profile)

    if "user-details" in request.POST:
        user_form = UserUpdateForm(request.POST, instance=user_instance)

        profile_form = ProfileUpdateForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            print("is_valid()", user_form.is_valid())
            user_form.save()

            # Manually handle phone number formatting before saving profile form
            phone_number = (profile_form.cleaned_data["phone_number"] or "").strip()

            # Ensure it starts with +61 and strip leading 0 if present
            if phone_number and not phone_number.startswith("+61"):
                phone_number = phone_number.lstrip("0")  # e.g. 0412... -> 412...
                profile.phone_number = "+61" + phone_number
            else:
                profile.phone_number = phone_number

            # Save rest of the profile form fields
            profile.phone_notifications_enabled = profile_form.cleaned_data[
                "phone_notifications_enabled"
            ]
            profile.email_notifications_enabled = profile_form.cleaned_data[
                "email_notifications_enabled"
            ]

            profile.save()
            messages.success(request, "User details updated successfully.")
            return redirect("profile_settings", profile_id=profile_id)
        else:
            print("is_valid()", user_form.is_valid())
    if "friend_visibility" in request.POST:
        if request.POST["friend_visibility"] == "hide":
            profile.friend_visibility = False
        else:
            profile.friend_visibility = True

        profile.save()
        messages.success(request, "Friend count visibility changed successfully.")
        return redirect("profile_settings", profile_id=profile_id)

    context = {
        "profile": profile,
        "user_form": user_form,
        "profile_form": profile_form,
    }

    return render(request, "app/settings.html", context)


@login_required
# @check_profile_id
def delete_account(request):
    profile = Profile.objects.get(user=request.user)

    # Check if the profile is hosting any future, non-cancelled events
    upcoming_events_host = Event.objects.filter(
        host=profile, event_date__gte=timezone.now(), cancelled=False
    )
    # Check if the profile is attending any future, non-cancelled events
    upcoming_events_attendee = Event.objects.filter(
        guests=profile, event_date__gte=timezone.now(), cancelled=False
    )

    # If the user is part of any future event, display a message and prevent deletion
    if upcoming_events_host.exists() or upcoming_events_attendee.exists():
        messages.error(
            request,
            "You are currently part of an upcoming event as a host or attendee. "
            "Please remove yourself from the event(s) before deleting your account.",
        )
        return redirect("home")

    # If no events are found, proceed with deletion
    if request.method == "POST":
        profile.delete()
        request.user.delete()
        logout(request)
        messages.success(
            request,
            "Your account and associated profile have been successfully deleted.",
        )
        return redirect("home")


@login_required
@check_profile_id
def crop_image(request, profile_id):
    if request.method == "POST":
        profile = request.user.profile
        image_file = request.FILES.get("profile_pic")

        if image_file:
            profile.profile_pic = image_file
            profile.save()

            return redirect(
                f"{reverse('profile', args=[profile_id])}?image_updated=true"
            )

    context = {
        "profile_id": profile_id,
    }

    return render(request, "app/crop_image.html", context)
