from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from . models import Notification

@login_required
def notifications(request):
    request_profile = request.user.profile
    notifications = request_profile.notification_set.filter(read=False).order_by('-timestamp')
    return render(request, 'notifications/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_as_read(request):
    request_profile = request.user.profile
    request_profile.notification_set.filter(read=False).update(read=True)
    return JsonResponse({'success': True})
