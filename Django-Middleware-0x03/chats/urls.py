from django.urls import path
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("Hello, World! This is a test page for middleware logging.")

def admin_view(request):
    return HttpResponse("Admin area - check logs for request details.")

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin_view, name='admin'),
    path('test/', home_view, name='test'),
]