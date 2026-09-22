# Create your views here.
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse

from .models import Notification
from .serializers import NotificationSerializer, NotificationCountSerializer

from drf_spectacular.utils import extend_schema

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

    @extend_schema(
            summary="mark notifications as read by admin."
    )
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


    @extend_schema(
            summary="count unread notifications by admin."
    )
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        serializer = NotificationCountSerializer({"unread_count": count})
        return Response(serializer.data)
    








def liveness(request):
    #this endpoint is used by Kubernetes
    return JsonResponse(
        {
            "status":"OK"
        }
    )


def readiness(request):
    checks = {}


    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "OK"   
    except Exception:
        checks["database"] = "FAILD!"    

    try:
        cache.set("healthcheck", "ok", timeout=10)    
        if cache.get("healthcheck") != "ok":
            raise RuntimeError("Redis read/write faild")
        checks["redis"] = "ok"
    except Exception:
            checks["redis"] = "failed"
    if all(status == "ok" for status in checks.values()):
                return JsonResponse({"status": "ready","checks": checks,})
    return JsonResponse({
         
        "status": "not_ready",
        "checks": checks,

    }, status=503)
