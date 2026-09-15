from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.apps import apps
import random

UserAccount = apps.get_model('accounts', 'UserAccount')
Venue = apps.get_model('venues', 'Venue')
Pitch = apps.get_model('venues', 'Pitch')


class Command(BaseCommand):
    help = 'Seed venues and pitches for load testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # ── Create manager users ──────────────────
        managers = []
        for i in range(5):
            phone = f"+9891234{i:05d}"
            user, created = UserAccount.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'name': f'Manager{i}',
                    'last_name': f'Test{i}',
                    'email': f'manager{i}@test.com',
                    'is_complex_manager': True,
                }
            )
            if created:
                user.set_password('StrongPass123!')
                user.save()
            managers.append(user)

        # ── Create venues ─────────────────────────
        venues = []
        for i, manager in enumerate(managers):
            venue, _ = Venue.objects.get_or_create(
                manager=manager,
                defaults={
                    'venue_name': f'Venue {i}',
                    'address': f'Address {i}',
                    'phone': f'0912{i:07d}',
                    'is_active': True,
                    'is_verified': True,
                    'slug': slugify(f'venue-{i}'),
                }
            )
            venues.append(venue)

        # ── Create pitches ────────────────────────
        sport_types = ['football', 'futsal', 'volleyball', 'tennis']
        surface_types = ['grass', 'artificial', 'parquet']

        for venue in venues:
            for j in range(10):
                Pitch.objects.get_or_create(
                    venue=venue,
                    pitch_name=f'Pitch {j}',
                    defaults={
                        'sport_type': random.choice(sport_types),
                        'surface_type': random.choice(surface_types),
                        'capacity': random.randint(10, 30),
                        'price_per_hour': random.randint(100, 500) * 1000,
                        'is_active': True,
                    }
                )

        count = Pitch.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Done. {count} pitches created.'))