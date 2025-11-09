from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Profile, StatusUpdate


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


# @receiver(post_save, sender=StatusUpdate)
# def create_photo_for_status_update(sender, instance, created, **kwargs):
#     if created and instance.image:
#         # If the status update was created and has an image, create a corresponding Photo
#         Photo.objects.create(
#             image=instance.image,
#             description=instance.content or "Image from status update",
#             profile=instance.profile,
#             status=instance,
#         )
