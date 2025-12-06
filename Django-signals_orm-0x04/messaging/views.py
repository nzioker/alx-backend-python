from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from .models import Message
from django.db.models import Prefetch, Q

@login_required
def delete_user_account(request):
    """View to handle user account deletion with confirmation"""
    if request.method == 'POST':
        user = request.user
        username = user.username
        
        # Delete the user (this will trigger the post_delete signal)
        user.delete()
        
        # Logout the user
        logout(request)
        
        messages.success(request, f"Account '{username}' has been deleted successfully. All associated data has been cleaned up.")
        return redirect('home')
    
    return render(request, 'messaging/delete_account_confirm.html')


@login_required
def threaded_conversation_view(request, message_id=None):
    """
    Display threaded conversations with optimized queries
    If message_id is provided, show that specific thread
    Otherwise, show all conversations for the user
    """
    user = request.user
    
    if message_id:
        # Fetch a specific message thread with all replies
        try:
            # Get the message with optimized queries
            message = Message.objects.select_related(
                'sender', 'receiver'
            ).prefetch_related(
                Prefetch(
                    'replies',
                    queryset=Message.objects.select_related('sender', 'receiver')
                    .prefetch_related('replies')
                    .order_by('timestamp')
                )
            ).get(
                id=message_id,
                # Ensure user is part of the conversation
                Q(sender=user) | Q(receiver=user)
            )
            
            # Get all replies recursively
            all_replies = get_all_replies_recursive(message)
            
            context = {
                'thread_start': message,
                'all_replies': all_replies,
                'current_user': user,
            }
            return render(request, 'messaging/threaded_conversation.html', context)
            
        except Message.DoesNotExist:
            # Message not found or user doesn't have permission
            return render(request, 'messaging/message_not_found.html')
    
    else:
        # Show all conversations for the user
        conversations = get_user_conversations(user)
        
        context = {
            'conversations': conversations,
            'current_user': user,
        }
        return render(request, 'messaging/conversation_list.html', context)

@login_required
def user_conversations_view(request):
    """
    Display all conversations for the logged-in user
    Uses Message.objects.filter() as required
    """
    user = request.user
    
    # Get all messages where user is sender or receiver
    messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=Message.objects.select_related('sender', 'receiver')
            .only('id', 'content', 'timestamp', 'sender__username', 'receiver__username')
        )
    ).order_by('-timestamp')
    
    # Organize by conversation partner
    conversations = {}
    for message in messages:
        # Determine conversation partner
        partner = message.receiver if message.sender == user else message.sender
        
        if partner.id not in conversations:
            conversations[partner.id] = {
                'partner': partner,
                'latest_message': message,
                'message_count': 0,
                'unread_count': 0,
            }
        
        conversations[partner.id]['message_count'] += 1
        
        # Count unread messages
        if not message.read and message.receiver == user:
            conversations[partner.id]['unread_count'] += 1
    
    context = {
        'conversations': list(conversations.values()),
        'current_user': user,
    }
    return render(request, 'messaging/conversations_overview.html', context)

def get_all_replies_recursive(message, depth=0, max_depth=10):
    """
    Recursively fetch all replies to a message
    Using Django ORM to avoid N+1 queries
    """
    if depth >= max_depth:
        return []
    
    # Fetch replies with optimized queries
    replies = message.replies.select_related(
        'sender', 'receiver'
    ).prefetch_related(
        Prefetch(
            'replies',
            queryset=Message.objects.select_related('sender', 'receiver')
            .only('id', 'content', 'timestamp', 'sender__username', 'receiver__username')
        )
    ).order_by('timestamp')
    
    # Process replies recursively
    result = []
    for reply in replies:
        reply_data = {
            'message': reply,
            'depth': depth + 1,
            'replies': get_all_replies_recursive(reply, depth + 1, max_depth)
        }
        result.append(reply_data)
    
    return result

def get_user_conversations(user):
    """
    Get all unique conversations for a user
    Optimized with select_related and prefetch_related
    """
    # Get all messages involving the user
    messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).select_related('sender', 'receiver').order_by('-timestamp')
    
    # Organize by conversation thread
    conversations = {}
    
    for message in messages:
        # For each message, get the conversation thread
        thread_root = get_thread_root(message)
        
        if thread_root.id not in conversations:
            # Fetch the entire thread with optimized queries
            thread_messages = Message.objects.filter(
                Q(id=thread_root.id) | Q(parent_message=thread_root)
            ).select_related(
                'sender', 'receiver'
            ).prefetch_related(
                Prefetch(
                    'replies',
                    queryset=Message.objects.select_related('sender', 'receiver')
                )
            ).order_by('timestamp')
            
            conversations[thread_root.id] = {
                'root_message': thread_root,
                'all_messages': thread_messages,
                'participants': set(),
                'message_count': thread_messages.count(),
                'latest_timestamp': thread_root.timestamp,
            }
        
        # Add participants
        conversations[thread_root.id]['participants'].add(message.sender)
        conversations[thread_root.id]['participants'].add(message.receiver)
        
        # Update latest timestamp
        if message.timestamp > conversations[thread_root.id]['latest_timestamp']:
            conversations[thread_root.id]['latest_timestamp'] = message.timestamp
    
    return conversations

def get_thread_root(message):
    """
    Find the root message of a thread by traversing parent_message links
    """
    current = message
    while current.parent_message:
        current = current.parent_message
    return current

@login_required
def reply_to_message(request, message_id):
    """
    Handle replying to a message
    """
    if request.method == 'POST':
        parent_message = get_object_or_404(
            Message.objects.select_related('sender', 'receiver'),
            id=message_id
        )
        
        content = request.POST.get('content', '').strip()
        
        if content:
            # Determine receiver - opposite of current user
            if request.user == parent_message.sender:
                receiver = parent_message.receiver
            else:
                receiver = parent_message.sender
            
            # Create reply
            reply = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content,
                parent_message=parent_message
            )
            
            # Optimize the response query
            # Use Message.objects.filter() to get updated thread
            thread_messages = Message.objects.filter(
                Q(id=parent_message.id) | Q(parent_message=parent_message)
            ).select_related('sender', 'receiver').order_by('timestamp')
            
            return render(request, 'messaging/thread_partial.html', {
                'messages': thread_messages,
                'current_user': request.user
            })
    
    return render(request, 'messaging/reply_form.html', {'message_id': message_id})


def unread_messages_view(request):
    """Display unread messages for the current user"""
    # Using custom manager with only() to select specific fields
    unread_messages = Message.unread_messages.for_user(request.user).only(
        'sender__username', 'content', 'timestamp'
    )
    
    context = {
        'unread_messages': unread_messages,
    }
    return render(request, 'messaging/unread_messages.html', context)