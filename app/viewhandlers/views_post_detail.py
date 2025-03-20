from django.shortcuts import get_object_or_404, render
from app.models import StatusUpdate


def post_detail(request, status_id):
    status = get_object_or_404(StatusUpdate, id=status_id)

    return render(request, "app/post-detail.html", {"status": status})
