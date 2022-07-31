import os

import os.path
from google.auth.transport.requests import Request
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class ServiceAccount:
    def __init__(self, client_secret_file, api_name, api_version, *scopes):
        self.service_account = None
        self.client_secret_file = client_secret_file
        self.api_name = api_name
        self.api_version = api_version
        self.scopes = scopes

    def Create_Service(self):

        CLIENT_SECRET_FILE = self.client_secret_file
        API_SERVICE_NAME = self.api_name
        API_VERSION = self.api_version
        SCOPES = self.scopes

        cred = None

        pickle_file = f'token_{API_SERVICE_NAME}_{API_VERSION}.pickle'

        if os.path.exists(pickle_file):
            with open(pickle_file, 'rb') as token:
                cred = pickle.load(token)

        if not cred or not cred.valid:
            if cred and cred.expired and cred.refresh_token:
                cred.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                cred = flow.run_local_server()

            with open(pickle_file, 'wb') as token:
                pickle.dump(cred, token)

        try:
            service = build(API_SERVICE_NAME, API_VERSION, credentials=cred)
            print(API_SERVICE_NAME, 'service created successfully')
            self.service_account = service
            return service
        except Exception as e:
            print('Unable to connect.')
            print(e)
            return None
        return dt

    def get_service_account(self):
        if not self.service_account:
            return "You dont have any service account set up yet! try calling create_service_account()"
        return self.service_account
