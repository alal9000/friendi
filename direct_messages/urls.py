from django.urls import path
from . import views

urlpatterns = [
  path('messages/<int:profile_id>', views.direct_messages, name='messages'),
  path('send_message/<int:profile_id>', views.send_message, name='send_message'),
  path('conversation/<int:sender_id>/<int:receiver_id>/', views.conversation_view, name='conversation'),
]