import logging
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class VenueCreateMixin:
    """
        Mixin for handling venue creation with custom logging and response format.
        Overrides default creation flow to provide structured responses and
        log both success and failure events.
    """
    def create(self, request, *args, **kwargs):
        """
            Validate input, create a venue instance, and return a formatted response.
            Logs validation errors and successful creations with user context.
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Venue creation failed by user {request.user.id} | errors: {serializer.errors}")
            return Response({
                "message": "Venue creation failed",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        logger.info(f"Venue created by user {request.user.id} | venue_id: {serializer.data.get('id')}")
        
        return Response({
            "message": "Venue created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)