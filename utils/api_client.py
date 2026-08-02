
import requests

class SwapiClient:
    def __init__(self, base_url="https://swapi.info/api"):
        self.base_url = base_url
        self.timeout = 10

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params, timeout=self.timeout)
        return response

    def get_by_url(self, full_url):
        return requests.get(full_url, timeout=self.timeout)