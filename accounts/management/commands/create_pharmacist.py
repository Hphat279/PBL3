from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Create a pharmacist user"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, required=True, help="Username")
        parser.add_argument("--password", type=str, required=True, help="Password")
        parser.add_argument("--email", type=str, default="", help="Email")
        parser.add_argument("--first_name", type=str, default="Dược sĩ", help="First name")
        parser.add_argument("--last_name", type=str, default="A", help="Last name")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]
        first_name = options["first_name"]
        last_name = options["last_name"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f"User with username '{username}' already exists."))
            return

        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role="pharmacist",
        )
        user.set_password(password)
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created pharmacist '{username}'.")
        )
