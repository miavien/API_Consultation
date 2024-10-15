from django.http import JsonResponse
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth = JWTAuthentication()

        user = None
        auth_result = None

        try:
            auth_result = auth.authenticate(request)
        except AuthenticationFailed:
            pass

        if auth_result:
            user, _ = auth_result
            if user.is_blocked:
                return JsonResponse({'error': 'Ваш аккаунт заблокирован'}, status=403)

        response = self.get_response(request)
        return response
