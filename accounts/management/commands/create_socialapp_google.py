from django.core.management.base import BaseCommand
from django.conf import settings
import os

try:
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
except Exception:
    SocialApp = None


class Command(BaseCommand):
    help = "Create or update Google SocialApp from environment variables"

    def handle(self, *args, **options):
        if SocialApp is None:
            self.stderr.write("django-allauth is not installed or SocialApp model not available.")
            return

        # Prefer values defined in Django settings, fallback to environment variables.
        client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", None) or os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        secret = getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", None) or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        name = getattr(settings, "GOOGLE_OAUTH_NAME", None) or os.environ.get("GOOGLE_OAUTH_NAME", "PBL3 Google")

        if not client_id or not secret:
            self.stderr.write("GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET not set; aborting.")
            return

        try:
            site = Site.objects.get(id=settings.SITE_ID)
        except Exception as e:
            self.stderr.write(f"Cannot find Site with id={settings.SITE_ID}: {e}")
            return

        sa, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={"name": name, "client_id": client_id, "secret": secret},
        )
        sa.sites.add(site)
        sa.save()

        self.stdout.write(self.style.SUCCESS(f"SocialApp google {'created' if created else 'updated'} (id={sa.id})"))
