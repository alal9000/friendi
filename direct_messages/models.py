from django.db import models
from app.models import Profile


class Message(models.Model):
    receiver = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="messaging"
    )
    message = models.TextField()
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="messager"
    )
    timestamp = models.DateTimeField()

    def __str__(self):
        return f"{self.sender}"


class Conversation(models.Model):
    participants = models.ManyToManyField(Profile, related_name="conversations")
    last_message = models.ForeignKey(
        "Message", null=True, blank=True, on_delete=models.SET_NULL
    )

    def get_other_participant(self, current_profile):
        for participant in self.participants.all():
            if participant != current_profile:
                return participant
        return None

    def __str__(self):
        return ", ".join(str(participant) for participant in self.participants.all())


class ConversationStatus(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="statuses")
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="conversation_statuses")
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.conversation} - {self.profile} (Deleted: {self.deleted})"
