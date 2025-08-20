import re
from django import forms
from django.forms import (
    ModelForm,
    TextInput,
    Textarea,
    EmailInput,
    NumberInput,
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from allauth.account.forms import (
    SignupForm,
    LoginForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
)

from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from .models import Profile, StatusUpdate, StatusComment
from events.models import Event


# create event
class EventForm(ModelForm):
    total_attendees = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=50,
        widget=NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Number of attendees inc host",
                "required": "true",
                "min": 1,
                "max": 50,
            }
        ),
        error_messages={
            "required": "Please enter the total number of attendees.",
            "min_value": "Attendees must be at least 1.",
            "max_value": "Attendees cannot exceed 50.",
        },
    )

    class Meta:
        model = Event
        fields = "__all__"
        exclude = ["user"]
        widgets = {
            "description": Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 500,
                    "class": "form-control",
                    "placeholder": "Write a description for your event",
                }
            ),
            "event_title": TextInput(
                attrs={"class": "form-control", "placeholder": "Name for your event"}
            ),
        }


# status update form
class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = StatusUpdate
        fields = ["content", "image"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "What's on your mind?",
                    "rows": 3,
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={"class": "form-control", "name": "status_image"}
            ),
        }
        labels = {"content": "", "image": "Optionally add an image"}


# status comment form
class StatusCommentForm(forms.ModelForm):
    class Meta:
        model = StatusComment
        fields = ["content"]


# update user info


def validate_name(value):
    print("validate_name ran")
    # Regex: start to end, only letters (a-zA-Z), hyphen (-), apostrophe ('), and spaces allowed
    if not re.fullmatch(r"[A-Za-z\-'\s]+", value):
        raise ValidationError(
            "First and last name can only contain letters, hyphens, apostrophes, and spaces."
        )


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=40,
        validators=[validate_name],
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    last_name = forms.CharField(
        max_length=60,
        validators=[validate_name],
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "email": EmailInput(attrs={"class": "form-control"}),
        }


# update user profile
class ProfileUpdateForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone_number",
            "phone_notifications_enabled",
            "email_notifications_enabled",
        ]
        widgets = {
            "phone_notifications_enabled": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "email_notifications_enabled": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


# profile description form
class ProfileDescriptionForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["description", "age_band"]
        labels = {"description": "About me", "age_band": "Age Band"}
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Location, hobbies, likes, dislikes...",
                    "rows": 5,
                    "cols": 40,
                    "class": "form-control placeholder-italic",
                }
            ),
            "age_band": forms.RadioSelect(),
        }


# invite friends to friendi
class InviteFriendForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter Email"}
        ),
    )


# hide and unhide friends
class FriendVisibilityForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["friend_visibility"]


# user signup
class CustomSignupForm(SignupForm):

    first_name = forms.CharField(max_length=50, label="First Name")
    last_name = forms.CharField(max_length=50, label="Last Name")
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        self.fields["first_name"].widget.attrs.update(
            {"class": "form-control mb-2", "placeholder": "First Name"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": "form-control mb-2", "placeholder": "Last Name"}
        )
        self.fields["email"].widget.attrs.update({"class": "form-control mb-2"})
        self.fields["password1"].widget.attrs.update({"class": "form-control mb-2"})
        self.fields["password2"].widget.attrs.update({"class": "form-control mb-2"})

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"].capitalize()
        user.last_name = self.cleaned_data["last_name"].capitalize()
        user.save()

        return user


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("username", None)
        self.fields["login"].widget.attrs.update({"class": "form-control mb-2"})
        self.fields["password"].widget.attrs.update({"class": "form-control"})


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"class": "form-control"})


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})
