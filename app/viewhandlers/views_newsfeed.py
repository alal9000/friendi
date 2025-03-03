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
def react_to_status(request, status_id, reaction_type):
    # Ensure that the reaction type is valid
    valid_reactions = ["like"]
    if reaction_type not in valid_reactions:
        return JsonResponse(
            {"success": False, "error": "Invalid reaction type"}, status=400
        )

    # Try to find the status update by the given id
    try:
        status_update = StatusUpdate.objects.get(id=status_id)
    except StatusUpdate.DoesNotExist:
        return JsonResponse({"success": False, "error": "Status not found"}, status=404)

    # Get the current user (who is reacting)
    user = request.user

    # Check if the user has already reacted to the status with the same reaction
    existing_reaction = Reaction.objects.filter(user=user, status=status_update).first()

    if existing_reaction and existing_reaction.reaction_type == "like":
        status_update.like_count -= 1

    # Create a new reaction if the user is reacting for the first time
    Reaction.objects.create(
        user=user, status=status_update, reaction_type=reaction_type
    )

    # Update the reaction counts based on the new reaction
    if reaction_type == "like":
        status_update.like_count += 1

    # Save the updated status update
    status_update.save()

    # Return a successful response with updated counts
    return JsonResponse(
        {
            "success": True,
            "status_id": status_update.id,
            "reaction_type": reaction_type,
            "like_count": status_update.like_count,
        }
    )
