from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from .models import Message
from django.db.models import Prefetch

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

def threaded_conversation_view(request, message_id):
    """Display a message with all its replies in threaded format"""
    # Using select_related and prefetch_related to optimize queries
    message = Message.objects.select_related('sender', 'receiver').get(id=message_id)
    
    # Prefetch all replies recursively
    def get_replies(message_obj):
        return message_obj.replies.select_related('sender', 'receiver').prefetch_related(
            Prefetch('replies', queryset=Message.objects.all().select_related('sender', 'receiver'))
        )
    
    replies = get_replies(message)
    
    context = {
        'message': message,
        'replies': replies,
    }
    return render(request, 'messaging/threaded_conversation.html', context)