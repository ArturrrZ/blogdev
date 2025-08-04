from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthenticationFromCookie(JWTAuthentication):
    def get_header(self, request):
        # This completely overrides the behavior of the base get_header()!
        token = request.COOKIES.get("access_token")
        if token:
            return f"Bearer {token}".encode()
        return None
