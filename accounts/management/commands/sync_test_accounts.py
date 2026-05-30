import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core import serializers
from django.utils import timezone
from accounts.models import User, Profile


class Command(BaseCommand):
    help = "Syncs test accounts between the local database and the fixtures/initial_data.json file safely."

    def handle(self, *args, **options):
        fixture_dir = os.path.join(settings.BASE_DIR, "fixtures")
        fixture_path = os.path.join(fixture_dir, "initial_data.json")

        self.stdout.write(self.style.WARNING("Starting test account synchronization..."))

        json_users = []
        json_profiles = []

        if os.path.exists(fixture_path):
            self.stdout.write(f"Reading existing fixtures from {fixture_path}...")
            try:
                # Detect encoding (usually UTF-8, but might be UTF-16 in some Windows redirect setups)
                with open(fixture_path, "rb") as f_raw:
                    raw_start = f_raw.read(2)
                encoding = "utf-16" if raw_start in (b"\xff\xfe", b"\xfe\xff") else "utf-8"

                with open(fixture_path, "r", encoding=encoding) as f:
                    json_data = json.load(f)

                # Filter items by model
                json_users = [item for item in json_data if item.get("model") == "accounts.user"]
                json_profiles = [item for item in json_data if item.get("model") == "accounts.profile"]
                self.stdout.write(self.style.SUCCESS(f"Loaded {len(json_users)} users and {len(json_profiles)} profiles from JSON."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading JSON fixture: {e}"))
                self.stdout.write("Proceeding to dump current local database to fixture instead.")
                json_users = []
                json_profiles = []
        else:
            self.stdout.write(self.style.WARNING(f"Fixture file not found at {fixture_path}. Will create a new one from local database."))

        # Map JSON users to their usernames and resolve any missing PKs
        json_pk_to_username = {}
        user_username_to_pk = {}

        explicit_pks = {u["pk"] for u in json_users if "pk" in u}
        next_pk = max(explicit_pks) + 1 if explicit_pks else 1

        for u in json_users:
            username = u["fields"]["username"]
            pk = u.get("pk")
            if pk is not None:
                json_pk_to_username[pk] = username
                user_username_to_pk[username] = pk
            else:
                # Check if user exists in local database
                db_user = User.objects.filter(username=username).first()
                if db_user:
                    pk = db_user.pk
                elif username.startswith("doctor") and username[6:].isdigit():
                    pk = int(username[6:])
                else:
                    pk = next_pk
                    next_pk += 1
                
                json_pk_to_username[pk] = username
                user_username_to_pk[username] = pk
                u["pk"] = pk

        # Map profiles in JSON to their usernames based on user FK
        profiles_by_username = {}
        for p in json_profiles:
            user_pk = p["fields"].get("user")
            if user_pk in json_pk_to_username:
                username = json_pk_to_username[user_pk]
                profiles_by_username[username] = p["fields"]

        # Sync JSON data into local database
        if json_users:
            self.stdout.write("Merging JSON accounts into local database...")
            users_created = 0
            users_updated = 0
            profiles_updated = 0

            with transaction.atomic():
                for u in json_users:
                    username = u["fields"]["username"]
                    user, created = User.objects.get_or_create(username=username)
                    
                    if created:
                        users_created += 1
                    else:
                        users_updated += 1

                    # Dynamically copy User fields
                    user_fields = [f.name for f in User._meta.fields if not f.primary_key and f.name != "username"]
                    for field_name in user_fields:
                        if field_name in u["fields"]:
                            setattr(user, field_name, u["fields"][field_name])
                    user.save()

                    # Update or create the profile
                    if username in profiles_by_username:
                        # Profile is automatically created by post_save signal when User is created,
                        # but we do get_or_create here to be absolutely safe
                        profile, _ = Profile.objects.get_or_create(user=user)
                        p_fields = profiles_by_username[username]
                        
                        profile_fields = [f.name for f in Profile._meta.fields if not f.primary_key and f.name != "user"]
                        for field_name in profile_fields:
                            f = Profile._meta.get_field(field_name)
                            attname = f.attname
                            if field_name in p_fields:
                                setattr(profile, attname, p_fields[field_name])
                        profile.save()
                        profiles_updated += 1

            self.stdout.write(self.style.SUCCESS(
                f"Database update complete: created {users_created} users, updated {users_updated} users, sync'd {profiles_updated} profiles."
            ))

        # Dump local database back to JSON fixture
        self.stdout.write("Writing complete merged data back to fixtures/initial_data.json...")
        try:
            os.makedirs(fixture_dir, exist_ok=True)
            
            # Fetch all users and profiles sorted by ID for clean and deterministic git diffs
            all_users = User.objects.all().order_by("id")
            all_profiles = Profile.objects.all().order_by("id")
            
            # Serialize
            serialized_data = serializers.serialize("json", list(all_users) + list(all_profiles), indent=4)
            
            # Write to file
            with open(fixture_path, "w", encoding="utf-8") as f:
                f.write(serialized_data)
                
            self.stdout.write(self.style.SUCCESS(
                f"Successfully saved {all_users.count()} users and {all_profiles.count()} profiles to {fixture_path}."
            ))
            self.stdout.write(self.style.SUCCESS("Synchronization finished successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to write fixture file: {e}"))
