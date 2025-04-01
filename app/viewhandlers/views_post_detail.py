import json
from django.http import JsonResponse
from app.models import StatusUpdate
from notifications.models import Notification
from app.models import StatusComment
from app.forms import StatusCommentForm
from django.shortcuts import get_object_or_404, render
from app.decorators import check_friendship_or_author
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required


@check_friendship_or_author
def post_detail(request, status_id):
    status = get_object_or_404(StatusUpdate, id=status_id)

    return render(request, "app/post-detail.html", {"status": status})


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

                # Prepare the response data, including the avatar URL
                avatar_url = (
                    comment.author.profile.profile_pic.url
                    if comment.author.profile.profile_pic
                    else "/static/images/default-avatar.png"
                )

                return JsonResponse(
                    {
                        "success": True,
                        "author": f"{request.user.first_name} {request.user.last_name}",
                        "content": comment.content,
                        "created_at": comment.created_at.strftime("%B %d, %Y %I:%M %p"),
                        "comment_id": comment.id,
                        "avatar_url": avatar_url,
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "error": form.errors}, status=400
                )
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
