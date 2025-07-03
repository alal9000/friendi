from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q

from .models import Message, Conversation, ConversationStatus
from app.decorators import check_profile_id
from app.models import Profile
from notifications.models import Notification
from friends.models import Friend


def are_friends(profile1, profile2):
    return Friend.objects.filter(
        (
            (Q(sender=profile1) & Q(receiver=profile2))
            | (Q(sender=profile2) & Q(receiver=profile1))
        )
        & Q(status="accepted")
    ).exists()


@login_required
@check_profile_id
def direct_messages(request, profile_id):
    current_profile = get_object_or_404(Profile, id=profile_id)

    if request.method == "POST":
        conversation_id = request.POST.get("conversation_id")
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            status, created = ConversationStatus.objects.get_or_create(
                conversation=conversation, profile=current_profile
            )
            status.deleted = True
            status.save()

            messages.success(request, "Conversation deleted successfully.")
            return redirect(reverse("messages", args=[profile_id]))

    all_conversations = Conversation.objects.filter(participants=current_profile)

    # Filter out conversations that have a status with deleted=True for the current profile
    deleted_conversations = ConversationStatus.objects.filter(
        profile=current_profile, deleted=True
    ).values_list("conversation", flat=True)

    conversations = all_conversations.exclude(id__in=deleted_conversations).distinct()

    # Prepare conversations data with the other participant
    conversations_data = [
        {
            "conversation": conversation,
            "other_participant": conversation.get_other_participant(current_profile),
        }
        for conversation in conversations
    ]

    context = {
        "conversations_data": conversations_data,
        "current_profile": current_profile,
    }

    return render(request, "direct_messages/messages.html", context)


@login_required
def send_message(request, profile_id):
    # Messages sent from recipients profile

    receiver_profile = get_object_or_404(Profile, id=profile_id)
    sender_profile = request.user.profile
    message_text = request.POST.get("message")

    if message_text:
        # Check if a conversation already exists between these participants
        conversation = (
            Conversation.objects.filter(participants=sender_profile)
            .filter(participants=receiver_profile)
            .first()
        )

        # If no conversation exists, create a new one
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(sender_profile, receiver_profile)

        message = Message.objects.create(
            conversation=conversation,
            sender=sender_profile,
            receiver=receiver_profile,
            message=message_text,
            timestamp=timezone.now(),
        )

        # Update the last_message pointer (optional but matches your model)
        conversation.last_message = message
        conversation.save()

        # Update or create the ConversationStatus for the receiver to mark as not deleted
        receiver_status, created = ConversationStatus.objects.get_or_create(
            conversation=conversation,
            profile=receiver_profile,
        )
        receiver_status.deleted = False
        receiver_status.save()

        Notification.objects.create(
            user=receiver_profile,
            message=f"You have a new message from {sender_profile}",
            link=f"/direct_messages/conversation/{sender_profile.id}/{receiver_profile.id}/",
        )
        messages.success(request, "Message sent successfully.")

        return redirect("home")

    else:
        messages.success(request, "Message did not send successfully.")
        return redirect("home")


@login_required
def conversation_view(request, sender_id, receiver_id):
    # page requester is the same as current_profile
    if request.user.profile.pk == int(receiver_id):
        sender_profile = get_object_or_404(Profile, id=sender_id)
        receiver_profile = get_object_or_404(Profile, id=receiver_id)

        # Check if sender and receiver are friends
        if not are_friends(sender_profile, receiver_profile):
            messages.error(request, "You must be friends to view this conversation.")
            return redirect("home")

        messages_sent_by_sender = Message.objects.filter(
            sender=sender_profile, receiver=receiver_profile
        )
        messages_sent_by_receiver = Message.objects.filter(
            sender=receiver_profile, receiver=sender_profile
        )
        conversation_messages = (
            # combine qsets with django union operator and order by latest message
            messages_sent_by_sender
            | messages_sent_by_receiver
        ).order_by("timestamp")

        if request.method == "POST":
            message_text = request.POST.get("message")

            if message_text:
                Message.objects.create(
                    sender=receiver_profile,
                    receiver=sender_profile,
                    message=message_text,
                    timestamp=timezone.now(),
                )

                # Check if a conversation already exists between these participants
                conversation = (
                    Conversation.objects.filter(participants=sender_profile)
                    .filter(participants=receiver_profile)
                    .first()
                )

                # If no conversation exists, create a new one
                if not conversation:
                    conversation = Conversation.objects.create()
                    conversation.participants.add(sender_profile, receiver_profile)

                # Update or create the ConversationStatus for the receiver to mark as not deleted
                receiver_status, created = ConversationStatus.objects.get_or_create(
                    conversation=conversation,
                    profile=sender_profile,
                )
                receiver_status.deleted = False
                receiver_status.save()

                Notification.objects.create(
                    user=sender_profile,
                    message=f"You have a new message from {receiver_profile}",
                    link=f"/direct_messages/conversation/{receiver_profile.id}/{sender_profile.id}/",
                )

            return redirect(
                "conversation",
                sender_id=sender_profile.id,
                receiver_id=receiver_profile.id,
            )

        return render(
            request,
            "direct_messages/conversation.html",
            {
                "messages": conversation_messages,
                "sender": sender_profile,
                "receiver": receiver_profile,
            },
        )
    else:
        return redirect("home")
