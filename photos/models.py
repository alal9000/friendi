from django.db import models
from app.models import Profile, StatusUpdate

# Create your models here.


class Photo(models.Model):
    image = models.ImageField(null=False, blank=False)
    description = models.TextField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    status = models.ForeignKey(
        StatusUpdate, on_delete=models.SET_NULL, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.description
