from django.db import models
from app.models import Profile, StatusUpdate
from django.utils import timezone

# Create your models here.


class Photo(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="gallery_photos"
    )
    image = models.ImageField(upload_to="profile_gallery/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.profile.user.username}'s Photo"
