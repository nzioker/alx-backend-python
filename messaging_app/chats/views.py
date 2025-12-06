from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import User, Conversation, Message
from .serializers import (
    ConversationSerializer, 
    MessageSerializer,
    ConversationCreateSerializer,
    MessageDetailSerializer
)
from .permissions import IsParticipantOfConversation, IsMessageSenderOrParticipant, CanSendMessage
from .pagination import MessagePagination, ConversationPagination
from .filters import MessageFilter, ConversationFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from messaging.models import Message
from django.contrib.auth.decorators import login_required
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from django.db.models import Q, Count, Prefetch



class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating conversations
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['participants_id__first_name', 'participants_id__last_name']
    ordering_fields = ['created_at', 'participants_id__first_name']
    filterset_class = ConversationFilter
    pagination_class = ConversationPagination
    
    def get_queryset(self):
        """Return conversations where the current user is the participant"""
        return Conversation.objects.filter(participants_id=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List conversations with pagination and filtering
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = Conversation.objects.create(
            participants_id=serializer.validated_data['participants_id']
        )
        
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsParticipantOfConversation().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsParticipantOfConversation().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSendMessage])
    def send_message(self, request, pk=None):
        conversation = get_object_or_404(Conversation, pk=pk)
        
        if not CanSendMessage().has_object_permission(request, self, conversation):
            return Response(
                {"detail": "You do not have permission to send messages to this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for a specific conversation with pagination and filtering
        """
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        messages = conversation.messages.all().order_by('sent_at')
        
        # Apply filtering to messages
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply pagination
        paginator = MessagePagination()
        paginated_messages = paginator.paginate_queryset(filtered_messages, request)
        
        serializer = MessageDetailSerializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating messages with pagination and filtering
    """
    permission_classes = [IsAuthenticated, IsMessageSenderOrParticipant]
    serializer_class = MessageDetailSerializer
    pagination_class = MessagePagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['message_body', 'sender_id__first_name', 'sender_id__last_name']
    ordering_fields = ['sent_at', 'sender_id__first_name']
    filterset_class = MessageFilter
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation_id__participants_id=self.request.user
        ).order_by('-sent_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MessageSerializer
        return MessageDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List messages with pagination and filtering
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = get_object_or_404(
            Conversation, 
            pk=serializer.validated_data['conversation_id'].conversation_id,
            participants_id=request.user
        )
        
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only edit your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only edit your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only delete your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        """
        Get all messages sent by the current user with pagination and filtering
        """
        messages = Message.objects.filter(sender_id=request.user).order_by('-sent_at')
        
        # Apply filtering
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply pagination
        paginator = MessagePagination()
        paginated_messages = paginator.paginate_queryset(filtered_messages, request)
        
        serializer = self.get_serializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent messages (last 10) for the current user
        """
        messages = self.get_queryset()[:10]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    

# Function-based view with cache_page
@login_required
@cache_page(60)  # 60 seconds cache timeout
@vary_on_cookie  # Vary cache based on user session
def cached_conversation_list(request):
    """
    Cached view for displaying list of conversations
    60 seconds cache timeout
    """
    user = request.user
    
    # Get conversations with optimized queries
    conversations = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=Message.objects.select_related('sender', 'receiver')
            .only('id', 'content', 'timestamp')
        )
    ).order_by('-timestamp')[:50]  # Limit to 50 most recent
    
    # Get unread count (not cached separately for freshness)
    unread_count = Message.unread.filter(receiver=user).count()
    
    # Get conversation statistics
    conversation_stats = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).aggregate(
        total_messages=Count('id'),
        unique_contacts=Count('sender', distinct=True) + Count('receiver', distinct=True) - 1,
    )
    
    context = {
        'conversations': conversations,
        'unread_count': unread_count,
        'stats': conversation_stats,
        'current_user': user,
    }
    
    return render(request, 'messaging/cached_conversation_list.html', context)

@login_required
@cache_page(60)  # 60 seconds cache timeout
@vary_on_cookie
def cached_thread_view(request, thread_id):
    """
    Cached view for displaying a specific thread
    60 seconds cache timeout
    """
    user = request.user
    
    # Get thread with all replies
    thread_messages = Message.objects.filter(
        Q(id=thread_id) | Q(parent_message_id=thread_id)
    ).filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=Message.objects.select_related('sender', 'receiver')
            .prefetch_related('replies')
        )
    ).order_by('timestamp')
    
    if not thread_messages.exists():
        return render(request, 'messaging/thread_not_found.html')
    
    # Organize messages in thread structure
    thread_root = thread_messages.filter(parent_message__isnull=True).first()
    
    context = {
        'thread_root': thread_root,
        'thread_messages': thread_messages,
        'current_user': user,
    }
    
    return render(request, 'messaging/cached_thread_detail.html', context)

# Class-based view with method_decorator for cache_page
@method_decorator([login_required, cache_page(60)], name='dispatch')
class CachedMessageListView(ListView):
    """
    Class-based view with caching for message list
    60 seconds cache timeout
    """
    model = Message
    template_name = 'messaging/cached_message_list.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        
        # Optimized queryset with select_related and prefetch_related
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            'replies'
        ).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = self.request.user
        
        # Get unread count (fresh, not cached)
        context['unread_count'] = Message.unread.filter(
            receiver=self.request.user
        ).count()
        
        return context

# View with manual cache control
@login_required
def cached_conversation_with_manual_control(request):
    """
    View that demonstrates manual cache control
    with automatic cache invalidation
    """
    user = request.user
    cache_key = f'user_conversations_{user.id}'
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Cache miss - compute the data
        conversations = Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver')[:20]
        
        # Prepare data for caching
        cached_data = {
            'conversations': list(conversations.values(
                'id', 'content', 'timestamp', 'read',
                'sender__username', 'receiver__username'
            )),
            'generated_at': timezone.now(),
        }
        
        # Store in cache for 60 seconds
        cache.set(cache_key, cached_data, 60)
    
    context = {
        'conversations': cached_data['conversations'],
        'cached_at': cached_data['generated_at'],
        'current_user': user,
        'is_cached': cache.get(cache_key) is not None,
    }
    
    return render(request, 'messaging/manual_cached_view.html', context)

# View with per-user cache invalidation
@login_required
def invalidate_user_cache(request):
    """
    View to manually invalidate cache for the current user
    """
    if request.method == 'POST':
        user = request.user
        
        # Clear all cache keys for this user
        cache_keys_to_delete = [
            f'user_conversations_{user.id}',
            f'user_{user.id}_unread_count',
            f'user_{user.id}_message_stats',
        ]
        
        for key in cache_keys_to_delete:
            cache.delete(key)
        
        # Also clear view cache by using a version parameter
        # In production, you'd use django-redis or similar for pattern deletion
        
        return render(request, 'messaging/cache_cleared.html', {
            'user': user,
        })
    
    return render(request, 'messaging/invalidate_cache_confirm.html')

# View that combines caching with custom manager
@login_required
@cache_page(60)  # 60 seconds cache timeout
def cached_unread_messages_view(request):
    """
    Cached view showing unread messages using custom manager
    60 seconds cache timeout
    """
    user = request.user
    
    # Use custom manager to get unread messages
    unread_messages = Message.unread.unread_for_user(user)[:20]  # Limit to 20
    
    # Get sender statistics
    sender_stats = {}
    for message in unread_messages:
        sender_id = message.sender.id
        if sender_id not in sender_stats:
            sender_stats[sender_id] = {
                'sender': message.sender,
                'count': 0,
                'latest': message.timestamp,
            }
        sender_stats[sender_id]['count'] += 1
        if message.timestamp > sender_stats[sender_id]['latest']:
            sender_stats[sender_id]['latest'] = message.timestamp
    
    context = {
        'unread_messages': unread_messages,
        'sender_stats': list(sender_stats.values()),
        'total_unread': Message.unread.filter(receiver=user).count(),
        'current_user': user,
    }
    
    return render(request, 'messaging/cached_unread_messages.html', context)