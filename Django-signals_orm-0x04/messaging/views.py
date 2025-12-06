from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.contrib import messages as django_messages

@login_required
def delete_user(request):
    """View to handle user account deletion"""
    if request.method == 'POST':
        user = request.user
        user.delete()
        django_messages.success(request, "Your account has been deleted successfully.")
        return redirect('home')
    return render(request, 'messaging/delete_user_confirm.html')