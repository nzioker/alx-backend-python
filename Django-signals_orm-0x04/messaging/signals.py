from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when a new message is sent"""
    if created:
        Notification.objects.create(
            user=instance.receiver,
            message=instance
        )

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """Log message content before it's edited"""
    if instance.pk:  # Existing message being updated
        try:
            old_message = Message.objects.get(pk=instance.pk)
            if old_message.content != instance.content:
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content
                )
                instance.edited = True
        except Message.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """Clean up related data when a user is deleted using Django's ORM"""
    Message.objects.filter(sender=instance).delete()
    Message.objects.filter(receiver=instance).delete()
    
    Notification.objects.filter(user=instance).delete()
    
    MessageHistory.objects.filter(changed_by=instance).delete()
    
    user_messages = Message.objects.filter(sender=instance)
    
    Notification.objects.filter(message__in=user_messages).delete()
    
    Message.objects.filter(edited_by=instance).update(edited_by=None)