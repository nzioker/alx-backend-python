from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.
class User(AbstractUser):
    user_id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(null=False)
    last_name = models.CharField(null=False)
    ROLE_CHOICES = [
            ('guest','Guest'),
            ('host', 'Host'),
            ('admin', 'Admin')
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='guest')
    email = models.EmailField(unique=True)
    password_hash = models.CharField(null=False)
    phone_number = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.model):
    message_id = models.CharField(primary_key=True, max_length=20)
    sender_id = models.ForeignKey(User)
    message_body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

class Conversation(models.model):
    conversation_id = models.CharField(primary_key=True)
    participants_id = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)