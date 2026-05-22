from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from accounts.models import User
from accounts.models import Profile


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        # pre-fill user with email and generated username from email local-part
        user = super().populate_user(request, sociallogin, data)
        email = data.get('email') or sociallogin.account.extra_data.get('email')
        if email:
            user.email = email
            base = email.split('@')[0]
            username = slugify(base) or 'user'
            orig = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{orig}{counter}"
                counter += 1
            user.username = username
        return user

    def is_open_for_signup(self, request, sociallogin):
        # allow automatic signup via social providers
        return True

    def pre_social_login(self, request, sociallogin):
        # If a user already exists with this social account's email, connect the social account
        # to the existing user to avoid asking the user to sign in again.
        if sociallogin.is_existing:
            return
        email = None
        if sociallogin.account and sociallogin.account.extra_data:
            email = sociallogin.account.extra_data.get('email')
        if not email:
            return
        try:
            user = User.objects.get(email__iexact=email)
            # Connect the social account to the existing user and mark the sociallogin as existing
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """Save a new social user. Ensure provider, unusable password and avatar_url set."""
        user = sociallogin.user
        # set provider from sociallogin
        user.provider = sociallogin.account.provider if getattr(sociallogin, 'account', None) else ''
        # let default save happen
        user = super().save_user(request, sociallogin, form)
        try:
            # ensure password is unusable for social accounts
            if sociallogin.account and sociallogin.account.provider:
                user.set_unusable_password()
                user.save()
            # save avatar_url to profile if provided
            picture = None
            try:
                picture = sociallogin.account.extra_data.get('picture')
            except Exception:
                picture = None
            if picture:
                prof, _ = Profile.objects.get_or_create(user=user)
                prof.avatar_url = picture
                prof.save()
        except Exception:
            pass
        return user
