import pytest
import requests

BASE_URL = "https://stg.asksina.ai/api"

class SinaAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.authenticate_as_guest()

    def authenticate_as_guest(self):
        try:
            response = self.session.post(f"{self.base_url}/auth/guest")
            if response.status_code in [200, 201]:
                data = response.json()
                token = data.get("token") or data.get("access_token")
                if token:
                    self.session.headers.update({"Authorization": f"Bearer {token}"})
        except Exception:
            pass

    def post(self, endpoint, payload=None):
        return self.session.post(f"{self.base_url}{endpoint}", json=payload)

    def stream_post(self, endpoint, payload=None):
        headers = self.session.headers.copy()
        headers["Accept"] = "text/event-stream"
        return self.session.post(f"{self.base_url}{endpoint}", json=payload, headers=headers, stream=True)

@pytest.fixture(scope="session")
def api_client():
    return SinaAPIClient(BASE_URL)