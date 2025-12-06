from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages

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