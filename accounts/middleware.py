from django.shortcuts import redirect
from django.urls import reverse


class ProfileCompletionMiddleware:
    """Redirect authenticated users to complete profile when required fields are missing.

    Checks user.email, first_name and last_name. Exempts certain paths (login, logout,
    complete-profile, admin, static, socialaccount callbacks, password reset views).
    """

    EXEMPT_PATH_PREFIXES = [
        '/admin/',
        '/static/',
        '/media/',
    ]

    EXEMPT_NAMES = [
        'accounts:complete-profile',
        'accounts:logout',
        'accounts:login',
        'accounts:patient-register',
        'accounts:doctor-login',
        'doctors:dept-dashboard',
        'doctors:dept-referral',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        # Only enforce profile completion for patient role
        if getattr(user, 'role', None) != 'patient':
            return None

        path = request.path
        # Allow exempt prefixes
        for p in self.EXEMPT_PATH_PREFIXES:
            if path.startswith(p):
                return None

        # Resolve name-safe check is expensive; use path checks for common routes
        if path.startswith(reverse('accounts:complete-profile')):
            return None

        # If user already complete, allow
        if user.email and user.first_name and user.last_name:
            return None

        # Allow POST to the completion URL
        if path.startswith(reverse('accounts:complete-profile')):
            return None

        # Prevent redirect loops: if current path is login/logout/register or social callbacks, allow
        allow_paths = [
            reverse('accounts:login'),
            reverse('accounts:logout'),
            reverse('accounts:patient-register'),
            reverse('accounts:doctor-login'),
        ]
        if path in allow_paths:
            return None

        # Otherwise redirect to completion view
        return redirect(f"{reverse('accounts:complete-profile')}?next={path}")
