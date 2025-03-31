import json
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from app.forms import StatusUpdateForm, StatusCommentForm
from app.models import StatusComment, StatusUpdate
from friends.models import Friend
from notifications.models import Notification


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
    status_updates = (
        StatusUpdate.objects.filter(profile__id__in=profiles_to_include)
        .prefetch_related("comments")
        .order_by("-date_posted")
    )

    # Handle image uploads
    if request.method == "POST":
        form = StatusUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            status_update = form.save(commit=False)
            status_update.profile = current_user_profile
            status_update.save()
            messages.success(request, "Status updated successfully!")
            return redirect("newsfeed")

    else:
        form = StatusUpdateForm()

    return render(request, "app/newsfeed.html", {"status_updates": status_updates})


@login_required
def react_to_status(request, status_id):
    try:
        status_update = StatusUpdate.objects.get(id=status_id)
    except StatusUpdate.DoesNotExist:
        return JsonResponse({"success": False, "error": "Status not found"}, status=404)

    user = request.user

    if user in status_update.liked_by.all():
        status_update.liked_by.remove(user)  # Unlike
        is_liked = False
    else:
        status_update.liked_by.add(user)  # Like
        is_liked = True

    return JsonResponse(
        {
            "success": True,
            "isLiked": is_liked,
            "like_count": status_update.like_count,
        }
    )


@login_required
def post_comment(request, status_id):
    if request.method == "POST":
        status = get_object_or_404(StatusUpdate, id=status_id)
        try:
            data = json.loads(request.body)
            form = StatusCommentForm(data)
            if form.is_valid():
                parent_comment_id = data.get("parent_comment_id")

                # Initialize parent_comment_author to None in case there is no parent comment
                parent_comment_author = None

                comment = form.save(commit=False)
                comment.status = status
                comment.author = request.user
                comment.save()

                # If it's a reply to another comment, get the parent comment and send a notification to its author
                if parent_comment_id and parent_comment_id != "0":
                    parent_comment = get_object_or_404(
                        StatusComment, id=parent_comment_id
                    )
                    parent_comment_author = parent_comment.author

                    # Send notification to the parent comment's author (if different from the current user)
                    if parent_comment_author and parent_comment_author != request.user:
                        parent_profile = parent_comment_author.profile
                        Notification.objects.create(
                            user=parent_profile,
                            message=f"@{request.user.first_name} {request.user.last_name} replied to your comment",
                            link=f"/post/{status.id}",
                        )

                # Send notification to the status author
                if request.user != status.profile.user and (
                    not parent_comment_author
                    or parent_comment_author != status.profile.user
                ):
                    Notification.objects.create(
                        user=status.profile,  # Status author
                        message=f"@{request.user.first_name} {request.user.last_name} commented on your status",
                        link=f"/post/{status.id}",
                    )

                return JsonResponse(
                    {
                        "success": True,
                        "author": f"{request.user.first_name} {request.user.last_name}",
                        "content": comment.content,
                        "created_at": comment.created_at.strftime("%B %d, %Y %I:%M %p"),
                        "comment_id": comment.id,
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": form.errors}, status=400
                )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
