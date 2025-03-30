from functools import wraps
from django.shortcuts import get_object_or_404, redirect

from app.models import StatusUpdate
from friends.models import Friend
from django.db.models import Q


def check_profile_id(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        profile_id_url = kwargs.get("profile_id")
        profile_id_request = request.user.profile.id

        if profile_id_url != profile_id_request:
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def check_friendship_or_author(view_func):
    def _wrapped_view(request, *args, **kwargs):
        status_id = kwargs.get("status_id")
        status = get_object_or_404(StatusUpdate, id=status_id)
        post_author = status.profile
        current_profile = request.user.profile

        # Get the list of friends of the post author
        friend_ids = Friend.objects.filter(
            Q(sender=post_author, status="accepted")
            | Q(receiver=post_author, status="accepted")
        ).values_list("sender", "receiver")

        friend_ids = set(
            [id for pair in friend_ids for id in pair if id != post_author.id]
        )

        # Check if the current user is the post author or one of their friends
        is_author = current_profile == post_author
        is_friend = current_profile.id in friend_ids

        if not is_author and not is_friend:
            # If the user is neither the author nor a friend, redirect them
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
