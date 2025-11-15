import re
import os
import environ
import logging
import stripe
from stripe import Webhook, SignatureVerificationError
from django.core.validators import validate_email
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils.text import capfirst
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.messages import get_messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from allauth.account.views import SignupView, LoginView
from django.db.models import Q, Count, F, Value
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from .models import NewsletterSignup, CheckoutSessionRecord
from notifications.models import Notification
from .forms import (
    CustomSignupForm,
    CustomLoginForm,
)
from events.models import Event

# Load the appropriate .env file
env = environ.Env()
if os.environ.get("DJANGO_ENV") != "production":
    env.read_env(".env.development")
else:
    env.read_env(".env.production")

# stripe config
stripe.api_key = env("STRIPE_SECRET_KEY")

# prepare logger
logger = logging.getLogger(__name__)


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
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()

        # Validate name: only letters, spaces, commas, hyphens allowed
        if not name:
            error = "Name cannot be blank."
            return render(
                request,
                "app/main.html",
                {"error": error, "name": name, "email": email},
            )

        if not re.match(r"^[A-Za-z ,\-]+$", name):
            error = "Name can only contain letters, spaces, commas, and hyphens."
            return render(
                request,
                "app/main.html",
                {"error": error, "name": name, "email": email},
            )

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            error = "Please enter a valid email address."
            return render(
                request,
                "app/main.html",
                {"error": error, "name": name, "email": email},
            )

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


def premium(request):
    return render(request, "app/premium.html")


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


# stripe views
def cancel(request):
    return render(request, "app/cancel.html")


def success(request):
    stripe_checkout_session_id = request.GET.get("session_id")
    context = {}

    if stripe_checkout_session_id:
        try:
            record = CheckoutSessionRecord.objects.get(
                stripe_checkout_session_id=stripe_checkout_session_id
            )
            context["user_email"] = record.user.email
            context["user_first_name"] = record.user.first_name
            context["status"] = "Payment successful!"
        except CheckoutSessionRecord.DoesNotExist:
            context["status"] = "Payment processed, but record not found yet."
    else:
        context["status"] = "No session ID provided."

    return render(request, "app/success.html", context)


@login_required(login_url="account_login")
def create_checkout_session(request):
    price_lookup_key = request.POST["price_lookup_key"]
    try:
        prices = stripe.Price.list(
            lookup_keys=[price_lookup_key], expand=["data.product"]
        )
        price_item = prices.data[0]

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {"price": price_item.id, "quantity": 1},
                # You could add differently priced services here, e.g., standard, business, first-class.
            ],
            mode="subscription",
            success_url=env("DOMAIN")
            + reverse("success")
            + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=env("DOMAIN") + reverse("cancel"),
            customer_email=request.user.email,
            metadata={
                "user_id": request.user.id,
            },
        )

        # We connect the checkout session to the user who initiated the checkout.
        CheckoutSessionRecord.objects.create(
            user=request.user,
            stripe_checkout_session_id=checkout_session.id,
            stripe_price_id=price_item.id,
        )

        return redirect(
            checkout_session.url, code=303  # Either the success or cancel url.
        )
    except Exception as e:
        print(e)
        return HttpResponse("Server error", status=500)


def portal(request):
    """
    Creates a customer portal for the user to manage their subscription.
    """
    checkout_record = (
        CheckoutSessionRecord.objects.filter(
            user=request.user,
            stripe_customer_id__isnull=False,
            stripe_customer_id__gt="",
            has_access=True,
            is_completed=True,
        )
        .order_by("-id")
        .first()
    )

    if not checkout_record:
        # Handle case where user has no active/completed subscription
        messages.error(request, "No active subscription found.")
        return redirect("home")

    checkout_session = stripe.checkout.Session.retrieve(
        checkout_record.stripe_checkout_session_id
    )

    portal_session = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=env("DOMAIN")
        + reverse("home"),  # Send the user here from the portal.
    )
    return redirect(portal_session.url, code=303)


@csrf_exempt
def collect_stripe_webhook(request):
    """
    Stripe sends webhook events to this endpoint.
    We verify the webhook signature and update the database record.
    """
    webhook_secret = env("STRIPE_WEBHOOK_SECRET").strip()
    signature = request.META["HTTP_STRIPE_SIGNATURE"]
    payload = request.body

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=webhook_secret
        )
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except SignatureVerificationError as e:
        return JsonResponse({"error": str(e)}, status=400)

    _update_record(event)

    return JsonResponse({"status": "success"})


def _update_record(webhook_event):
    """
    We update our database record based on the webhook event.

    Use these events to update your database records.
    You could extend this to send emails, update user records, set up different access levels, etc.
    """
    data_object = webhook_event["data"]["object"]
    event_type = webhook_event["type"]

    if event_type == "checkout.session.completed":
        user_id = data_object["metadata"].get("user_id")

        if user_id:
            user = User.objects.get(id=user_id)

            try:
                checkout_record = CheckoutSessionRecord.objects.get(
                    stripe_checkout_session_id=data_object["id"]
                )
            except CheckoutSessionRecord.DoesNotExist:
                logger.warning(f"No checkout session found for {data_object.get('id')}")
                return
            except CheckoutSessionRecord.MultipleObjectsReturned:
                logger.error(
                    f"Multiple checkout records found for {data_object.get('id')}"
                )
                return

            checkout_record.user = user
            checkout_record.stripe_customer_id = data_object["customer"]
            checkout_record.has_access = True
            checkout_record.is_completed = True
            checkout_record.save()

            # Update profile
            profile = checkout_record.user.profile
            profile.is_premium = True
            profile.save()

    elif event_type == "invoice.payment_failed":
        # Payment failed for an existing subscription (renewal, etc.)
        customer_id = data_object["customer"]
        checkout_record = CheckoutSessionRecord.objects.filter(
            stripe_customer_id__isnull=False,
            stripe_customer_id__gt="",
            stripe_customer_id=customer_id,
        ).last()

        if checkout_record:
            checkout_record.has_access = False
            checkout_record.save()

            profile = checkout_record.user.profile
            profile.is_premium = False
            profile.save()

            send_mail(
                subject="Your friendi Premium payment failed",
                message="We couldn't process your latest payment. Please update your card details on your profile user settings.",
                from_email="support@friendi.com",
                recipient_list=[checkout_record.user.email],
            )

    elif event_type == "invoice.payment_succeeded":
        if data_object.get("billing_reason") == "subscription_create":
            return

        customer_id = data_object["customer"]
        checkout_record = CheckoutSessionRecord.objects.filter(
            stripe_customer_id__isnull=False,
            stripe_customer_id__gt="",
            stripe_customer_id=customer_id,
        ).last()

        if checkout_record:
            checkout_record.has_access = True
            checkout_record.save()

            profile = checkout_record.user.profile
            profile.is_premium = True
            profile.save()

            send_mail(
                subject="Your friendi Premium payment succeeded",
                message="Your friendi Premium subscription has been renewed successfully!",
                from_email="support@friendi.com",
                recipient_list=[checkout_record.user.email],
            )

    elif event_type == "customer.subscription.deleted":

        try:
            checkout_record = CheckoutSessionRecord.objects.get(
                stripe_customer_id=data_object["customer"]
            )
        except CheckoutSessionRecord.DoesNotExist:
            logger.warning(
                f"No checkout session found for {data_object.get('customer')}"
            )
            return
        except CheckoutSessionRecord.MultipleObjectsReturned:
            logger.error(
                f"Multiple checkout records found for {data_object.get('customer')}"
            )
            return

        checkout_record.has_access = False
        checkout_record.save()

        # Update profile
        profile = checkout_record.user.profile
        profile.is_premium = False
        profile.save()


# end stripe views


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

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


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

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
