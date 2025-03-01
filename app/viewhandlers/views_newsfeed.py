from django.http import JsonResponse
from django.shortcuts import redirect, render

from app.models import Reaction, StatusUpdate
from friends.models import Friend

def newsfeed(request):
    if not request.user.is_authenticated:
        return redirect("account_login")

    current_user_profile = request.user.profile  # Get the logged-in user's profile

    # Get a list of friend profile IDs
    sender_friends = list(Friend.objects.filter(
        sender=current_user_profile, status="accepted"
    ).values_list("receiver_id", flat=True))

    receiver_friends = list(Friend.objects.filter(
        receiver=current_user_profile, status="accepted"
    ).values_list("sender_id", flat=True))

    # Combine both lists and include the current user
    profiles_to_include = sender_friends + receiver_friends + [current_user_profile.id]

    # Get status updates from both the user and their friends
    status_updates = StatusUpdate.objects.filter(profile__id__in=profiles_to_include).order_by('-date_posted')

    # Calculate reaction counts for each status
    for status in status_updates:
        status.heart_count = status.total_reactions('heart')
        status.laugh_count = status.total_reactions('laugh')
        status.fire_count = status.total_reactions('fire')

    return render(request, "app/newsfeed.html", {"status_updates": status_updates})


def react_to_status(request, status_id, reaction_type):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "message": "User not logged in."}, status=401)

        try:
            status = StatusUpdate.objects.get(id=status_id)
        except StatusUpdate.DoesNotExist:
            return JsonResponse({"success": False, "message": "Status not found."}, status=404)

        # Ensure user can react multiple times with different reactions
        reaction, created = Reaction.objects.get_or_create(
            user=request.user, status=status, reaction_type=reaction_type
        )

        if created:
            toggled_off = False
        else:
            # If reaction exists, toggle it off (remove it)
            reaction.delete()
            toggled_off = True

        # Get updated reaction count
        count = status.total_reactions(reaction_type)

        return JsonResponse({
            "success": True,
            "reaction": None if toggled_off else reaction_type,
            "count": count
        })

    return JsonResponse({"success": False, "message": "Invalid request."}, status=400)