from notifications.models import Notification

def notifications_count(request):
    unread_count = 0
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user.profile, read=False).count()
    return {'unread_count': unread_count}