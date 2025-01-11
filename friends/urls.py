from django.urls import path
from . import views

urlpatterns = [
  path('<int:profile_id>/', views.friends, name="friends"),
  path('friend_requests/<int:profile_id>/', views.friend_requests, name='friend_requests'),
  
]