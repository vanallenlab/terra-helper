import google.auth
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.cloud import storage


class Google:
    credentials_file = "credentials.json"

    @classmethod
    def get_credentials(cls, credentials=None):
        if os.path.exists(cls.credentials_file):
            credentials = Credentials.from_authorized_user_file(cls.credentials_file)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                credentials, project = google.auth.default()
                credentials.refresh(Request())
            with open(cls.credentials_file, 'w') as credentials_file:
                credentials_file.write(credentials.to_json())
        return credentials

    @classmethod
    def get_token(cls):
        credentials = cls.get_credentials()
        return credentials.token

    @staticmethod
    def refresh_token(credentials):
        credentials.refresh(Request())


class Storage(Google):
    @classmethod
    def create_client(cls):
        credentials = cls.get_credentials()
        return storage.Client(credentials=credentials)
