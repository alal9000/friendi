from django.urls import path

from app.viewhandlers import views_newsfeed
from app.viewhandlers import views_profile
from . import views
from .views import CustomSignupView, CustomLoginView

urlpatterns = [
    path("", views.home, name="home"),
    path("about", views.about, name="about"),
    path("newsletter/signup", views.newsletter_signup, name="newsletter_signup"),
    path("thank-you", views.thank_you, name="thank-you"),
    path("recommendations", views.recommendations, name="recommendations"),
    path("contact", views.contact, name="contact"),
    path("faqs", views.faqs, name="faqs"),
    path("delete-your-data", views.data_delete, name="data_delete"),
    path("privacy-policy", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service", views.tos, name="tos"),
    path("search_events", views.search_events, name="search_events"),
    path("delete-account", views_profile.delete_account, name="delete_account"),
    # newsfeed urls
    path("newsfeed", views_newsfeed.newsfeed, name="newsfeed"),
    path(
        "react/<int:status_id>/", views_newsfeed.react_to_status, name="react_to_status"
    ),
    path(
        "post_comment/<int:status_id>/",
        views_newsfeed.post_comment,
        name="post_comment",
    ),
    # all_auth urls
    path("accounts/login", CustomLoginView.as_view(), name="account_login"),
    path("accounts/signup", CustomSignupView.as_view(), name="account_signup"),
    path("accounts/profile/<int:profile_id>", views_profile.profile, name="profile"),
    path(
        "accounts/profile/<int:profile_id>/settings",
        views_profile.profile_settings,
        name="profile_settings",
    ),
]
