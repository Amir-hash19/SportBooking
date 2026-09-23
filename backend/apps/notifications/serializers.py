from rest_framework import serializers
from .models import Notification



class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification. Only `is_read` is writable."""
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "notification_type", "link", "is_read", "created_at"]
        read_only_fields = ["id", "title", "message", "notification_type", "link", "created_at"]


class NotificationCountSerializer(serializers.Serializer):
    """Serializer for returning the count of unread notifications."""
    unread_count = serializers.IntegerField()




