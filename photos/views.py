from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from app.models import Profile
from .models import Photo


def gallery(request, profile_id):
    profile = get_object_or_404(Profile, id=profile_id)

    photos = Photo.objects.filter(profile=profile)

    # Photos Pagination
    photos_per_page = 20
    paginator = Paginator(photos, photos_per_page)
    page_number = request.GET.get("page")

    try:
        photos = paginator.page(page_number)
    except PageNotAnInteger:
        photos = paginator.page(1)
    except EmptyPage:
        photos = paginator.page(paginator.num_pages)

    context = {
        "photos": photos,
        "profile": profile,
    }

    return render(request, "photos/gallery.html", context)


def viewPhoto(request, profile_id, photo_id):
    profile = get_object_or_404(Profile, id=profile_id)
    photo = get_object_or_404(Photo, id=photo_id, profile=profile)

    context = {"photo": photo, "profile": profile}

    return render(request, "photos/photo.html", context)
