from django.http import JsonResponse


class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and user.is_blocked:
            return JsonResponse({'error': 'Ваш аккаунт заблокирован'}, status=403)
        response = self.get_response(request)
        return response
