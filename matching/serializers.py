from rest_framework import serializers
from .models import Interaction, Match, Notification


class InteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interaction
        fields = ["id", "from_user", "to_user", "action", "created_at"]
        read_only_fields = ["from_user", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "created_at", "is_read"]
