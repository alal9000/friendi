import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from app.models import Reaction, StatusUpdate
from friends.models import Friend
from django.db.models import F


def newsfeed(request):
    if not request.user.is_authenticated:
        return redirect("account_login")

    current_user_profile = request.user.profile  # Get the logged-in user's profile

    # Get a list of friend profile IDs
    sender_friends = list(
        Friend.objects.filter(
            sender=current_user_profile, status="accepted"
        ).values_list("receiver_id", flat=True)
    )

    receiver_friends = list(
        Friend.objects.filter(
            receiver=current_user_profile, status="accepted"
        ).values_list("sender_id", flat=True)
    )

    # Combine both lists and include the current user
    profiles_to_include = sender_friends + receiver_friends + [current_user_profile.id]

    # Get status updates from both the user and their friends
    status_updates = StatusUpdate.objects.filter(
        profile__id__in=profiles_to_include
    ).order_by("-date_posted")

    return render(request, "app/newsfeed.html", {"status_updates": status_updates})


@login_required
def react_to_status(request, status_id):
    try:
        status_update = StatusUpdate.objects.get(id=status_id)
    except StatusUpdate.DoesNotExist:
        return JsonResponse({"success": False, "error": "Status not found"}, status=404)

    user = request.user

    # Check if a like already exists
    reaction, created = Reaction.objects.get_or_create(user=user, status=status_update)

    if created:
        reaction.is_liked = True  # First time liking
        status_update.like_count += 1  # Increment like count
    else:
        reaction.is_liked = not reaction.is_liked  # Toggle like
        status_update.like_count += 1 if reaction.is_liked else -1  # Adjust count

    # Save the objects
    reaction.save()
    status_update.save()

    # Return a successful response with updated counts
    return JsonResponse(
        {
            "success": True,
            "isLiked": reaction.is_liked,
            "like_count": status_update.like_count,
        }
    )
