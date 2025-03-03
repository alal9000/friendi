from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.models import User
from PIL import Image, ImageOps
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F

AGE_BAND_CHOICES = [
    ("rather_not_say", "Rather not say"),
    ("under_25", "Under 25"),
    ("25_to_35", "25 - 35"),
    ("36_and_over", "36 and over"),
]


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        default="placeholder/profile2.png", null=True, blank=True
    )
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    friend_visibility = models.BooleanField(default=True, null=True)
    age_band = models.CharField(
        max_length=20,
        choices=AGE_BAND_CHOICES,
        null=True,
        blank=False,
        default="rather_not_say",
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    # Resize the profile picture to 350x350 px
    def save(self, *args, **kwargs):
        # Skip save logic if profile is being created with the default picture
        if (
            self.pk
            and self.profile_pic
            and self.profile_pic.name != "placeholder/profile2.png"
        ):
            img = Image.open(self.profile_pic)

            # Apply the EXIF orientation to fix rotation issues
            img = ImageOps.exif_transpose(img)

            # Convert to RGB to ensure compatibility with JPEG format
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Resize only if the image is larger than the target size
            if img.height > 350 or img.width > 350:
                output_size = (350, 350)
                img.thumbnail(output_size)

                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                buffer.seek(0)

                # Replace the profile_pic content
                self.profile_pic.save(
                    self.profile_pic.name, ContentFile(buffer.read()), save=False
                )

        # Save only once after processing
        super().save(*args, **kwargs)


class StatusUpdate(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="status_updates"
    )
    content = models.TextField(blank=True, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-date_posted"]


class Reaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.ForeignKey(
        StatusUpdate, on_delete=models.CASCADE, related_name="reactions"
    )
    is_liked = models.BooleanField(default=False)

    def __str__(self):
        return (
            f"{self.user.username} {'liked' if self.liked else 'unliked'} {self.status}"
        )


class NewsletterSignup(models.Model):
    email = models.EmailField(
        unique=True
    )  # Ensure the email is unique to avoid duplicates
    name = models.CharField(
        max_length=100, blank=True, null=True
    )  # Optional field for the user's name
    date_signed_up = models.DateTimeField(
        auto_now_add=True
    )  # Automatically set the date when the signup occurs

    def __str__(self):
        return self.email
