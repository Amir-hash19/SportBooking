# Create your views here.
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer, NotificationCountSerializer


class NotificationListView(ListAPIView):
    """List notifications for the authenticated user. Filter by ?is_read=true/false."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs


class NotificationMarkReadView(APIView):
    """Mark a single notification as read. Returns 404 if not found or not owned by user."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(APIView):
    """Mark all unread notifications as read. Returns count of updated records."""
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"marked_read": updated})


class NotificationUnreadCountView(APIView):
    """Return the count of unread notifications for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        serializer = NotificationCountSerializer({"unread_count": count})
        return Response(serializer.data)