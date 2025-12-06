from django.db import models

class UnreadMessagesManager(models.Manager):
    """Custom manager for unread messages"""
    
    def get_queryset(self):
        return super().get_queryset().filter(read=False)
    
    def for_user(self, user):
        """Get unread messages for a specific user"""
        return self.get_queryset().filter(receiver=user).select_related('sender')