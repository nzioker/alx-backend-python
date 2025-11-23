from django.urls import path
from django.http import JsonResponse
from datetime import datetime

def home_view(request):
    return JsonResponse({
        'message': 'Welcome to the messaging app!',
        'current_time': datetime.now().isoformat(),
        'status': 'active'
    })

def messaging_view(request):
    return JsonResponse({
        'message': 'This is the messaging interface',
        'current_time': datetime.now().isoformat(),
        'status': 'active'
    })

def admin_view(request):
    return JsonResponse({
        'message': 'Admin area',
        'current_time': datetime.now().isoformat(),
        'status': 'active'
    })

def check_access_view(request):
    current_time = datetime.now().time()
    is_restricted = False
    
    # Check if current time is within restricted hours (9PM to 6AM)
    restricted_start = datetime.strptime('21:00', '%H:%M').time()
    restricted_end = datetime.strptime('06:00', '%H:%M').time()
    
    if restricted_start <= restricted_end:
        is_restricted = restricted_start <= current_time <= restricted_end
    else:
        is_restricted = current_time >= restricted_start or current_time <= restricted_end
    
    return JsonResponse({
        'current_time': current_time.isoformat(),
        'is_restricted': is_restricted,
        'restricted_hours': '9:00 PM - 6:00 AM',
        'message': 'Access restricted' if is_restricted else 'Access allowed'
    })

def rate_limit_info_view(request):
    from chats.middleware import RateLimitMiddleware
    middleware = RateLimitMiddleware()
    ip_address = middleware.get_client_ip(request)
    info = middleware.get_rate_limit_info(ip_address)
    return JsonResponse(info)

def permission_info_view(request):
    from chats.middleware import RolePermissionMiddleware
    middleware = RolePermissionMiddleware()
    permissions_info = middleware.get_user_permissions_info(request)
    return JsonResponse(permissions_info)

def public_api_view(request):
    return JsonResponse({
        'message': 'Public API endpoint - accessible to all authenticated users',
        'status': 'public'
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin_view, name='admin'),
    path('api/messages/', messaging_view, name='messaging'),
    path('api/conversations/', messaging_view, name='conversations'),
    path('check-access/', check_access_view, name='check_access'),
    path('rate-limit-info/', rate_limit_info_view, name='rate_limit_info'),
    path('permissions/info/', permission_info_view, name='permission_info'),
]