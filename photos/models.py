from django.db import models
from app.models import Profile
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile

# Create your models here.


class GalleryPhoto(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="gallery_photos"
    )
    image = models.ImageField(upload_to="profile_gallery/")
    thumbnail = models.ImageField(
        upload_to="profile_gallery/thumbnails/", blank=True, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def save(self, *args, **kwargs):
        # Only generate thumbnail if image is present
        if self.image:
            img = Image.open(self.image)
            img = ImageOps.exif_transpose(img)  # fix rotation

            if img.mode != "RGB":
                img = img.convert("RGB")

            # Fixed width thumbnail
            fixed_width = 400
            w_percent = fixed_width / float(img.width)
            new_height = int(float(img.height) * w_percent)
            img = img.resize((fixed_width, new_height), Image.LANCZOS)

            # Save thumbnail to memory
            thumb_io = BytesIO()
            img.save(thumb_io, format="JPEG")
            thumb_name = f"thumb_{self.image.name.split('/')[-1]}"
            self.thumbnail.save(
                thumb_name, ContentFile(thumb_io.getvalue()), save=False
            )

        # Call original save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.profile.user.username}'s Photo"


class Album(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name


class AlbumPhoto(models.Model):
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(null=False, blank=False)
    description = models.TextField()
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.description
