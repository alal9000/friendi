from datetime import datetime
from django.utils.text import capfirst
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from allauth.account.views import SignupView, LoginView
from django.db.models import Q, Count, F, Value
from django.db.models.functions import Coalesce

from .models import NewsletterSignup
from notifications.models import Notification
from .forms import (
    CustomSignupForm,
    CustomLoginForm,
)
from events.models import Event
from django.contrib.auth.models import User


# function based views
def home(request):
    current_datetime = datetime.now()
    unread_count = 0
    if request.user.is_authenticated:
        user = request.user.profile
        unread_count = Notification.objects.filter(user=user, read=False).count()

    # filter out events that are past their starting time and that are full / need understanding for this
    all_events = (
        Event.objects.annotate(
            num_guests=Count("guests"),
            num_attendees=Coalesce(
                F("num_guests") + Value(1), Value(0)
            ),  # add 1 for the host
        )
        .filter(cancelled=False)
        .filter(locked=False)
        .filter(
            Q(event_date__gt=current_datetime.date())
            | Q(
                event_date=current_datetime.date(),
                event_time__gte=current_datetime.time(),
            )
        )
        .filter(
            Q(total_attendees__isnull=True) | Q(num_attendees__lt=F("total_attendees"))
        )
        .order_by("-date_created")
    )
    # pagination logic
    events_per_page = 9
    paginator = Paginator(all_events, events_per_page)
    page_number = request.GET.get("page")

    try:
        events = paginator.page(page_number)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    # end

    # message logic
    storage = get_messages(request)
    success_message = None
    for message in storage:
        if message.tags == "success":
            success_message = message
    # end

    context = {
        "events": events,
        "success_message": success_message,
        "unread_count": unread_count,
    }

    return render(request, "app/dashboard.html", context)


def search_events(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        # Filter by search and exclude cancelled or locked
        events = Event.objects.filter(
            Q(event_title__icontains=searched)
            | Q(host__user__first_name__icontains=searched)
            | Q(host__user__last_name__icontains=searched),
            cancelled=False,
            locked=False,
        )

        # filter out expired events in Python using the property
        active_events = [event for event in events if not event.expired]

        context = {"searched": searched, "events": active_events}
        return render(request, "app/search_events.html", context)
    else:
        return render(request, "app/search_events.html")


def newsletter_signup(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")

        if User.objects.filter(email=email).exists():
            return render(
                request,
                "app/email_in_use.html",
                {"message": "This email is already registered."},
            )

        NewsletterSignup.objects.create(email=email, name=name)

        return render(request, "app/thank-you.html")


def recommendations(request):
    return render(request, "app/recommendations.html")


def about(request):
    return render(request, "app/about.html")


def get_started(request):
    return render(request, "app/get-started.html")


def contact(request):
    return render(request, "app/contact.html")


def feedback(request):
    return render(request, "app/feedback.html")


def faqs(request):
    return render(request, "app/faqs.html")


def data_delete(request):
    return render(request, "app/data.html")


def privacy_policy(request):
    return render(request, "app/privacy.html")


def thank_you(request):
    return render(request, "app/thank-you.html")


def tos(request):
    return render(request, "app/terms_of_service.html")


# class based views
class CustomSignupView(SignupView):
    form_class = CustomSignupForm
    template_name = "account/signup.html"
    default_success_url = reverse_lazy("home")

    def get_success_url(self):
        return self.default_success_url

    def form_valid(self, form):
        form.cleaned_data["first_name"] = capfirst(form.cleaned_data["first_name"])
        form.cleaned_data["last_name"] = capfirst(form.cleaned_data["last_name"])

        response = super().form_valid(form)

        first_name = form.cleaned_data.get("first_name")
        messages.success(
            self.request,
            f"Welcome, {first_name}! Your account was created successfully.",
        )

        return response


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = "account/login.html"

    def get_success_url(self):
        return reverse_lazy("home")

    def form_valid(self, form):
        response = super().form_valid(form)
        first_name = self.request.user.first_name

        messages.success(
            self.request, f"Welcome, {first_name}! You have successfully logged in."
        )

        return response
