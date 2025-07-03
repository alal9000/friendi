from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden

from app.decorators import check_profile_id
from django.contrib.auth.decorators import login_required

from direct_messages.models import Conversation
from .models import Friend
from notifications.models import Notification
from app.models import Profile


def friends(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    friends = Friend.objects.filter(
        Q(sender=profile, status="accepted") | Q(receiver=profile, status="accepted")
    )

    other_friends = [friend.get_other_profile(profile) for friend in friends]

    # Sort the other_friends queryset alphabetically by the first name
    other_friends = sorted(other_friends, key=lambda x: x.user.first_name)

    # unfriend
    if request.method == "POST":
        if request.user.profile != profile:
            return HttpResponseForbidden("You are not allowed to unfriend this user.")

        friend_id = request.POST.get("friend_id")
        friend_profile = get_object_or_404(Profile, id=friend_id)

        # Remove the friendship
        Friend.objects.filter(
            Q(sender=profile, receiver=friend_profile)
            | Q(sender=friend_profile, receiver=profile)
        ).delete()

        # Remove the conversation between them if it exists
        conversation = (
            Conversation.objects.filter(participants=profile)
            .filter(participants=friend_profile)
            .first()
        )
        if conversation:
            conversation.delete()  # deletes conversation and auto-cascades messages

        messages.success(request, "Friend removed successfully")
        return redirect("friends", profile_id=profile_id)
    # end unfriend

    return render(
        request, "friends/friends.html", {"friends": other_friends, "profile": profile}
    )


@login_required
@check_profile_id
def friend_requests(request, profile_id):
    request_profile = request.user.profile
    if request.method == "POST":
        friend_request_id = request.POST.get("friend_request_id")
        action = request.POST.get("action")

        if friend_request_id and action:
            friend_request = get_object_or_404(
                Friend, id=friend_request_id, receiver=request_profile
            )

            if action == "approve":
                friend_request.status = "accepted"
                friend_request.save()

                Notification.objects.create(
                    user=friend_request.sender,
                    message=f"Your friend request to {friend_request.receiver} was accepted",
                    link=reverse("profile", args=[request.user.profile.id]),
                )
                messages.success(request, "Friend request approved.")
            elif action == "deny":
                friend_request.status = "denied"
                friend_request.save()
                messages.success(request, "Friend request denied.")

        return redirect("profile", profile_id)

    requests = Friend.objects.filter(status="pending", receiver=request_profile)

    context = {
        "requests": requests,
    }

    return render(request, "friends/friend_requests.html", context)
