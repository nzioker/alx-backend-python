from rest_framework import authentication
from rest_framework import exceptions
from .models import User

class CustomTokenAuthentication(authentication.TokenAuthentication):
    
    def authenticate_credentials(self, key):
        try:
            from rest_framework.authtoken.models import Token
            token = Token.objects.select_related('user').get(key=key)
            user = token.user
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')
        
        if not user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')
            
        return (user, token)

class JWTAuthentication(authentication.BaseAuthentication):
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(user_id=user_id)
            return (user, token)
        except Exception as e:
            raise exceptions.AuthenticationFailed('Invalid JWT token')

def get_user_from_token(token):
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        return User.objects.get(user_id=user_id)
    except Exception as e:
        return None

def create_jwt_token_for_user(user):
    
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }