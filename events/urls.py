from django.urls import path
from . import views

urlpatterns = [
    path("event/<int:event_id>", views.event, name="event"),
    path(
        "event/<int:profile_id>/manage_requests",
        views.event_requests,
        name="event_requests",
    ),
    path(
        "event/<int:event_id>/remove_attendee",
        views.remove_attendee,
        name="remove_attendee",
    ),
    path("event/<int:event_id>/cancel", views.cancel_event, name="cancel_event"),
    path("create", views.create, name="create"),
    path(
        "<int:event_id>/send_invite", views.send_event_invite, name="send_event_invite"
    ),
]
