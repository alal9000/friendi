from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from app.models import Profile


class Event(models.Model):
    event_title = models.CharField(max_length=300)
    total_attendees = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=300, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    event_date = models.DateField(null=True, blank=False)
    event_time = models.TimeField(null=True, blank=False)
    description = models.TextField()
    host = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_host",
    )
    date_created = models.DateTimeField(auto_now_add=True, blank=True)
    guests = models.ManyToManyField(Profile, related_name="attended_events", blank=True)
    cancelled = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)

    def __str__(self):
        return self.event_title

    @property
    def expired(self):
        if self.event_date and self.event_time:
            event_datetime = datetime.combine(self.event_date, self.event_time)
            event_datetime = timezone.make_aware(
                event_datetime, timezone.get_current_timezone()
            )
            return timezone.now() > (event_datetime + timedelta(hours=1))
        return False

    @property
    def available_guest_slots(self):
        return max(self.total_attendees - 1 - self.guests.count(), 0)

    @property
    def pending_guest_requests(self):
        return self.event_requests.filter(status="pending").count()

    @property
    def is_fully_booked_or_locked(self):
        return (
            self.locked
            or (self.available_guest_slots - self.pending_guest_requests) <= 0
        )


class EventComment(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    comment = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, blank=True)

    def __str__(self):
        return f"{self.comment}"


class EventRequest(models.Model):
    host = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="event_request_host"
    )
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="event_requests_sent"
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_requests"
    )
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("denied", "Denied"),
        ],
        default="pending",
    )

    def __str__(self):
        return f"{self.sender} -> {self.event} ({self.status})"
