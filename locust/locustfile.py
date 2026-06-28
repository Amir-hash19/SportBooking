import random
import string
import logging
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def random_phone():
    """Generate a random 11-digit Iranian-style phone number."""
    return "+9809" + "".join(random.choices(string.digits, k=9))

def random_string(length=8):
    return "".join(random.choices(string.ascii_lowercase, k=length))


# ─────────────────────────────────────────
# Unauthenticated User
# ─────────────────────────────────────────

class UnauthenticatedUser(HttpUser):
    """
    Simulates anonymous users browsing public endpoints.
    No token required.
    Weight=2 → 2 out of every 3 virtual users are anonymous.
    """
    weight = 2
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    @task(5)
    def list_venues(self):
        """GET /api/v1/venues/ — public venue listing."""
        with self.client.get(
            "/api/v1/venues/",
            name="/api/v1/venues/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Expected 200, got {resp.status_code}")

    @task(3)
    def retrieve_pitch(self):
        """GET /api/v1/pitch/<pk>/ — public pitch detail."""
        pk = random.randint(1, 50)   # adjust range to your seed data
        with self.client.get(
            f"/api/v1/pitch/{pk}/",
            name="/api/v1/pitch/[pk]/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(1)
    def signup_new_user(self):
        """POST /api/v1/user/signup/ — register a brand-new user."""
        phone = random_phone()
        payload = {
            "name": random_string(),
            "last_name": random_string(),
            "phone_number": phone,
            "email": f"{random_string()}@test.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        with self.client.post(
            "/api/v1/user/signup/",
            json=payload,
            name="/api/v1/user/signup/",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                resp.success()
            elif resp.status_code == 409:
                # duplicate — acceptable under high concurrency
                resp.success()
            else:
                resp.failure(f"Signup failed: {resp.status_code} — {resp.text[:120]}")


# ─────────────────────────────────────────
# Authenticated User
# ─────────────────────────────────────────

class AuthenticatedUser(HttpUser):
    """
    Simulates logged-in users hitting protected endpoints.
    Each VU registers + logs in during on_start, then uses the JWT.
    Weight=1 → 1 out of every 3 virtual users is authenticated.
    """
    weight = 1
    wait_time = between(1, 4)
    host = "http://localhost:8000"

    def on_start(self):
        """Called once per virtual user at spawn time."""
        self.token = None
        self._register_and_login()

    # ── Auth flow ────────────────────────

    def _register_and_login(self):
        phone = random_phone()
        password = "StrongPass123!"

        # 1. Register
        signup_payload = {
            "name": random_string(),
            "last_name": random_string(),
            "phone_number": phone,
            "email": f"{random_string()}@test.com",
            "password": password,
            "password_confirm": password,
        }
        with self.client.post(
            "/api/v1/user/signup/",
            json=signup_payload,
            name="/api/v1/user/signup/ [setup]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                # signup already returns tokens — use them directly
                data = resp.json()
                self.token = data.get("tokens", {}).get("access")
                resp.success()
                if self.token:
                    return   # no need to call login separately
            else:
                resp.failure(f"Setup signup failed: {resp.status_code}")

        # 2. Login (fallback or if signup didn't return a token)
        login_payload = {
            "phone_number": phone,
            "password": password,
        }
        with self.client.post(
            "/api/v1/user/login/",
            json=login_payload,
            name="/api/v1/user/login/ [setup]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("data", {}).get("access")
                resp.success()
            else:
                resp.failure(f"Setup login failed: {resp.status_code}")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    # ── Tasks ────────────────────────────

    @task(4)
    def list_venues_authenticated(self):
        """GET /api/v1/venues/ — same public endpoint, measured separately."""
        with self.client.get(
            "/api/v1/venues/",
            headers=self._auth_headers(),
            name="/api/v1/venues/ [auth]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"Expected 200, got {resp.status_code}")

    @task(3)
    def retrieve_pitch_authenticated(self):
        pk = random.randint(1, 50)
        with self.client.get(
            f"/api/v1/pitch/{pk}/",
            headers=self._auth_headers(),
            name="/api/v1/pitch/[pk]/ [auth]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def list_users(self):
        """GET /api/v1/user/list/ — requires auth."""
        with self.client.get(
            "/api/v1/user/list/",
            headers=self._auth_headers(),
            name="/api/v1/user/list/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Expected 200/403, got {resp.status_code}")

    @task(1)
    def admin_list_requests(self):
        """GET /api/v1/admin/list/requests/ — admin only, 403 is valid for normal users."""
        with self.client.get(
            "/api/v1/admin/list/requests/",
            headers=self._auth_headers(),
            name="/api/v1/admin/list/requests/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Unexpected {resp.status_code}")


# ─────────────────────────────────────────
# Event hooks (optional logging)
# ─────────────────────────────────────────

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if not isinstance(environment.runner, MasterRunner):
        logger.info("🚀 Load test starting — SportBooking API")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("✅ Load test finished")