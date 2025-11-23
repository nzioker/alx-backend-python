import django_filters
from django_filters import rest_framework as filters
from .models import Message, Conversation, User
from django.db import models
import datetime

class MessageFilter(filters.FilterSet):
    """
    Filter class for messages to retrieve conversations with specific users 
    or messages within a time range
    """
    
    # Filter by conversation
    conversation = django_filters.ModelChoiceFilter(
        field_name='conversation_id',
        queryset=Conversation.objects.all(),
        label='Conversation'
    )
    
    # Filter by sender
    sender = django_filters.ModelChoiceFilter(
        field_name='sender_id',
        queryset=User.objects.all(),
        label='Sender'
    )
    
    # Filter by message content (case-insensitive contains)
    message_body = django_filters.CharFilter(
        field_name='message_body',
        lookup_expr='icontains',
        label='Message Contains'
    )
    
    # Date range filtering for sent_at
    sent_after = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='gte',
        label='Sent After'
    )
    
    sent_before = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='lte',
        label='Sent Before'
    )
    
    # Today's messages
    today = django_filters.BooleanFilter(
        method='filter_today',
        label="Today's Messages"
    )
    
    # Recent messages (last 7 days)
    recent = django_filters.BooleanFilter(
        method='filter_recent',
        label="Recent Messages (7 days)"
    )
    
    class Meta:
        model = Message
        fields = {
            'conversation_id': ['exact'],
            'sender_id': ['exact'],
            'message_body': ['icontains'],
            'sent_at': ['gte', 'lte', 'exact'],
        }
    
    def filter_today(self, queryset, name, value):
        """
        Filter messages from today
        """
        if value:
            today = datetime.date.today()
            return queryset.filter(sent_at__date=today)
        return queryset
    
    def filter_recent(self, queryset, name, value):
        """
        Filter messages from the last 7 days
        """
        if value:
            week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            return queryset.filter(sent_at__gte=week_ago)
        return queryset

class ConversationFilter(filters.FilterSet):
    """
    Filter class for conversations
    """
    
    # Filter by participant
    participant = django_filters.ModelChoiceFilter(
        field_name='participants_id',
        queryset=User.objects.all(),
        label='Participant'
    )
    
    # Filter by creation date range
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created Before'
    )
    
    # Filter by participant's role
    participant_role = django_filters.ChoiceFilter(
        field_name='participants_id__role',
        choices=User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [],
        label='Participant Role'
    )
    
    # Has messages filter
    has_messages = django_filters.BooleanFilter(
        method='filter_has_messages',
        label='Has Messages'
    )
    
    class Meta:
        model = Conversation
        fields = {
            'participants_id': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
        }
    
    def filter_has_messages(self, queryset, name, value):
        """
        Filter conversations that have messages
        """
        if value is not None:
            if value:
                return queryset.filter(messages__isnull=False).distinct()
            else:
                return queryset.filter(messages__isnull=True)
        return queryset

class UserFilter(filters.FilterSet):
    """
    Filter class for users
    """
    
    # Filter by role
    role = django_filters.ChoiceFilter(
        choices=User.ROLE_CHOICES if hasattr(User, 'ROLE_CHOICES') else [],
        label='Role'
    )
    
    # Filter by email (case-insensitive contains)
    email = django_filters.CharFilter(
        field_name='email',
        lookup_expr='icontains',
        label='Email Contains'
    )
    
    # Filter by name (first or last name contains)
    name = django_filters.CharFilter(
        method='filter_name',
        label='Name Contains'
    )
    
    # Date range filtering for created_at
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created Before'
    )
    
    class Meta:
        model = User
        fields = {
            'role': ['exact'],
            'email': ['exact', 'icontains'],
            'first_name': ['icontains'],
            'last_name': ['icontains'],
            'created_at': ['gte', 'lte', 'exact'],
        }
    
    def filter_name(self, queryset, name, value):
        """
        Filter by first name or last name containing the value
        """
        if value:
            return queryset.filter(
                models.Q(first_name__icontains=value) | 
                models.Q(last_name__icontains=value)
            )
        return queryset