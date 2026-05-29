import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings

try:
    from allauth.socialaccount.models import SocialApp
except ImportError:
    SocialApp = None


class Command(BaseCommand):
    help = "Create Google SocialApp for django-allauth using environment variables"

    def handle(self, *args, **options):
        if not SocialApp:
            self.stdout.write(
                self.style.ERROR(
                    "django-allauth is not installed or configured properly."
                )
            )
            return

        # Fetch environment variables
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    "Error: GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET environment variables are missing."
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "Please set them in your terminal before running this command."
                )
            )
            return

        # Get the site (settings.SITE_ID is 2)
        site_id = getattr(settings, "SITE_ID", 1)
        try:
            site = Site.objects.get(pk=site_id)
        except Site.DoesNotExist:
            # If site with ID doesn't exist, get or create it
            site, created = Site.objects.get_or_create(
                pk=site_id,
                defaults={
                    "domain": "127.0.0.1:8000",
                    "name": "Localhost",
                },
            )
            self.stdout.write(
                self.style.WARNING(
                    f"Created Site with ID {site_id} as it did not exist."
                )
            )

        # Create or update the SocialApp
        app, created = SocialApp.objects.get_or_create(
            provider="google",
            defaults={
                "name": "Google",
                "client_id": client_id,
                "secret": client_secret,
            },
        )

        if not created:
            app.client_id = client_id
            app.secret = client_secret
            app.save()
            self.stdout.write(
                self.style.SUCCESS("Updated existing Google SocialApp configuration.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Created new Google SocialApp configuration.")
            )

        # Associate with the site
        app.sites.add(site)
        self.stdout.write(
            self.style.SUCCESS(
                f"Linked Google SocialApp to site: {site.domain} (ID: {site.id})"
            )
        )
