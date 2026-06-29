import random
import logging

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

logger = logging.getLogger(__name__)


class UnauthenticatedUser(HttpUser):
    """
    Simulates anonymous users reading public APIs only.
    """
    weight = 2
    wait_time = between(0.5, 1.5)
    host = "http://web:8000"

    @task(5)
    def retrieve_pitch(self):
        pk = random.randint(2, 51)

        with self.client.get(
            f"/api/v1/pitch/{pk}/",
            name="/api/v1/pitch/[pk]/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")




class AuthenticatedUser(HttpUser):
    """
    Uses one existing account.
    No signup during load test.
    """
    weight = 1
    wait_time = between(0.5, 1.5)
    host = "http://web:8000"

    def on_start(self):
        self.token = None
        self.login()

    def login(self):

        payload = {
                    "phone_number":"+989223296493",
                    "password":"Amir112233@"
                }

        response = self.client.post(
            "/api/v1/user/login/",
            json=payload,
            name="/api/v1/user/login/",
        )

        if response.status_code == 200:
            data = response.json()

            self.token = (
                data.get("tokens", {}).get("access")
                or data.get("data", {}).get("access")
                or data.get("access")
            )

        if not self.token:
            logger.error("Login failed")

    def headers(self):
        return (
            {"Authorization": f"Bearer {self.token}"}
            if self.token
            else {}
        )


    @task(2)
    def list_venues(self):
        with self.client.get(
            "/api/v1/venues/",
            name="/api/v1/venues/",
            headers=self.headers(),
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")


    @task(5)
    def retrieve_pitch(self):
        pk = random.randint(2, 51)

        with self.client.get(
            f"/api/v1/pitch/{pk}/",
            headers=self.headers(),
            name="/api/v1/pitch/[pk]/ [auth]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")

    @task(2)
    def users(self):
        with self.client.get(
            "/api/v1/user/list/",
            headers=self.headers(),
            name="/api/v1/user/list/",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 403):
                resp.success()
            else:
                resp.failure(f"Unexpected status {resp.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    if not isinstance(environment.runner, MasterRunner):
        logger.info("Load test started")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test finished")