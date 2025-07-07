from django.utils import timezone
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.models import User
from PIL import Image, ImageOps

AGE_BAND_CHOICES = [
    ("rather_not_say", "Leave blank"),
    ("under_25", "Under 25"),
    ("25_to_35", "25 - 35"),
    ("36_and_over", "36 and over"),
]


class Profile(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        default="placeholder/profile2.png",
        null=True,
        blank=True,
    )
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    phone_notifications_enabled = models.BooleanField(default=False)
    email_notifications_enabled = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    friend_visibility = models.BooleanField(default=True, null=True)
    has_seen_tour = models.BooleanField(default=False)
    age_band = models.CharField(
        max_length=20,
        choices=AGE_BAND_CHOICES,
        null=True,
        blank=False,
        default="rather_not_say",
    )

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def active_hosted_events_count(self):
        """Count future non-cancelled events this user is hosting."""
        now = timezone.now().date()
        return self.event_host.filter(cancelled=False, event_date__gte=now).count()

    def active_attending_events_count(self):
        """Count future non-cancelled events this user is attending as guest."""
        now = timezone.now().date()
        return self.attended_events.filter(cancelled=False, event_date__gte=now).count()

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
    image = models.ImageField(upload_to="status_images/", blank=True, null=True)
    liked_by = models.ManyToManyField(User, related_name="liked_statuses", blank=True)

    class Meta:
        ordering = ["-date_posted"]

    @property
    def like_count(self):
        return self.liked_by.count()


class StatusComment(models.Model):
    status = models.ForeignKey(
        StatusUpdate, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.status.id}"


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
