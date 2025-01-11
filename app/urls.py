from django.urls import path
from . import views
from . views import CustomSignupView, CustomLoginView

urlpatterns = [
  path('', views.home, name="home"),
  path('about', views.about, name="about"),
  path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
  path('thank-you', views.thank_you, name="thank-you"),
  path('recommendations', views.recommendations, name="recommendations"),
  path('contact', views.contact, name="contact"),
  path('faqs', views.faqs, name="faqs"),
  path('delete-your-data', views.data_delete, name="data_delete"),
  path('privacy-policy', views.privacy_policy, name="privacy_policy"),
  path('terms-of-service', views.tos, name="tos"),
  path('search_events', views.search_events, name="search_events"),
  path('delete-account', views.delete_account, name="delete_account"),

  # all_auth urls
  path('accounts/login', CustomLoginView.as_view(), name='account_login'),
  path('accounts/signup', CustomSignupView.as_view(), name='account_signup'),
  path('accounts/profile/<int:profile_id>', views.profile, name='profile'),
  path('accounts/profile/<int:profile_id>/settings', views.profile_settings, name='profile_settings'),
]

