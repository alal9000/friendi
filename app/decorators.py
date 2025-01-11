from functools import wraps
from django.shortcuts import redirect


def check_profile_id(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        profile_id_url = kwargs.get("profile_id")
        profile_id_request = request.user.profile.id

        if profile_id_url != profile_id_request:
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return _wrapped_view
