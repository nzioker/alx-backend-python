from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .managers import UnreadMessagesManager

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True) 
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_messages') 
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    objects = models.Manager()  
    unread_messages = UnreadMessagesManager()  

    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user} about message {self.message.id}"
    
class MessageHistory(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='history')
    old_content = models.TextField()
    changed_at = models.DateTimeField(default=timezone.now)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"History for message {self.message.id}"