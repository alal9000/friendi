from django.urls import path

from app.viewhandlers import views_newsfeed, views_profile, views_post_detail
from . import views
from .views import CustomSignupView, CustomLoginView

urlpatterns = [
    path("", views.home, name="home"),
    path("about", views.about, name="about"),
    path("get-started", views.get_started, name="start"),
    path("newsletter/signup", views.newsletter_signup, name="newsletter_signup"),
    path("thank-you", views.thank_you, name="thank-you"),
    path("recommendations", views.recommendations, name="recommendations"),
    path("contact", views.contact, name="contact"),
    path("premium", views.premium, name="premium"),
    path("feedback", views.feedback, name="feedback"),
    path("faqs", views.faqs, name="faqs"),
    path("delete-your-data", views.data_delete, name="data_delete"),
    path("privacy-policy", views.privacy_policy, name="privacy_policy"),
    path("terms-of-service", views.tos, name="tos"),
    path("search_events", views.search_events, name="search_events"),
    path("delete-account", views_profile.delete_account, name="delete_account"),
    path(
        "remove-gallery-image/",
        views_profile.remove_gallery_image,
        name="remove_gallery_image",
    ),
    path("crop_image/<int:profile_id>", views_profile.crop_image, name="crop_image"),
    # newsfeed urls
    # path("newsfeed", views_newsfeed.newsfeed, name="newsfeed"),
    # path("post/<int:status_id>", views_post_detail.post_detail, name="post_detail"),
    # path(
    #     "react/<int:status_id>/", views_newsfeed.react_to_status, name="react_to_status"
    # ),
    # path(
    #     "post_comment/<int:status_id>/",
    #     views_post_detail.post_comment,
    #     name="post_comment",
    # ),
    # all_auth urls
    path("accounts/login", CustomLoginView.as_view(), name="account_login"),
    path("accounts/signup", CustomSignupView.as_view(), name="account_signup"),
    path("accounts/profile/<int:profile_id>", views_profile.profile, name="profile"),
    path(
        "accounts/profile/<int:profile_id>/settings",
        views_profile.profile_settings,
        name="profile_settings",
    ),
    # stripe urls
    path("cancel", views.cancel, name="cancel"),
    path("success", views.success, name="success"),
    path(
        "create-checkout-session",
        views.create_checkout_session,
        name="create-checkout-session",
    ),
    path(
        "portal",
        views.portal,
        name="portal",
    ),
    path(
        "collect-stripe-webhook",
        views.collect_stripe_webhook,
        name="collect-stripe-webhook",
    ),
    # end stripe urls
]
