from django.db import models
from app.models import Profile

class Notification(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255)  
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message