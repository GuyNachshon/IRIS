from __future__ import print_function
import io
import os.path
from googleapiclient.errors import HttpError
import os
from googleapiclient.http import MediaIoBaseDownload
from common import utils

creds = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
folder_id = os.environ["FOLDER_ID"]
SCOPES = ['https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = "drive"
API_VERSION = "v3"
VIDEOS_PATH = "/experiments"


def download_file(real_file_id, service):
    try:
        # create gmail api client
        file_id = real_file_id
        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file.getvalue()


def retrieve_all_files(service):
    query = f"parents='{folder_id}'"
    response = service.files().list(q=query).execute()
    files = response.get('files')
    nextPageToken = response.get('nextPageToken')
    while nextPageToken:
        response = service.files().list(q=query).execute()
        files.extend(response.get('nextPageToken'))
    return files


def main():
    print("building drive services")
    sa = utils.ServiceAccount(creds, API_SERVICE_NAME, API_VERSION, SCOPES)
    print("Service account initiated")
    utils.ServiceAccount.Create_Service(sa)
    print("service account built")
    service_account = utils.ServiceAccount.get_service_account()
    files = retrieve_all_files(service_account)
    download_count = 0
    for file in files:
        full_path = os.path.join(VIDEOS_PATH, file['name'])
        if os.path.exists(full_path):
            print(f"file {file['name']} already exists")
            continue
        download_file(file["id"], service_account)
        f = open(full_path, 'w')
        f.close()
        download_count += 1
    print(f"done, downloaded {download_count} files")


if __name__ == "__main__":
    main()
