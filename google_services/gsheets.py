from __future__ import print_function
import json
import pandas as pd
import os
from utils import common

SCOPES = ['https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = "102gqwAE6OIiAcAbT0boNx20oaXvOdX0-2Oj_fKUOoLo"
creds = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
API_SERVICE_NAME = "sheets"
API_VERSION = "v4"


def sheet_properties(title, **sheetProperties):
    defultProperties = {
        'properties': {
            'title': title,
            'index': 0,
            'sheetType': 'GRID',
            'hidden': False
        }
    }
    defultProperties['properties'].update(sheetProperties)
    return defultProperties


def add_sheet(service, sheetProperties, sheet_name):
    request = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID, ranges=[], includeGridData=False)
    sheet_metadata = request.execute()
    sheet_exists = False
    for sheet in sheet_metadata['sheets']:
        if sheet['properties']['title'] == sheet_name:
            sheet_exists = True
    if sheet_exists:
        return False
    request_body = {
        'requests': [{
            'addSheet': sheetProperties(sheet_name)
        }]
    }
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=request_body
    ).execute()

    print(f"added sheet response: \n{response}")


def format_data(json_location):
    with open(json_location, 'r') as f:
        df = pd.DataFrame()
        data = json.load(f)
        print(data)
        all = [["transcription accuracy", "color name", "start time stamp in seconds", "end time stamp in seconds"]]
        color_nums = []
        color_names = []
        color_names_conf = []
        start = []
        end = []
        for color in data:
            curr_all = []
            curr_color_name = []
            curr_color_name_conf = []
            color_nums.append(data[color]["color_num"])
            if 'transcript' in data[color].keys():
                for transcript in data[color]["transcript"]:
                    curr_color_name.append(transcript[1])
                    curr_color_name_conf.append(transcript[0])
                    curr_all.append(transcript[1])
                    curr_all.append(transcript[0])
            else:
                curr_color_name.append("UNKNOWN")
                curr_color_name_conf.append(0)
                curr_all.append("UNKNOWN")
                curr_all.append(0)
            color_names.append(curr_color_name)
            color_names_conf.append(curr_color_name_conf)
            if data[color]['start_ts']:
                start.append(data[color]['start_ts'] / 60)
                curr_all.append(data[color]['start_ts'] / 60)
            else:
                start.append(data[color]['start_ts'])
                curr_all.append(data[color]['start_ts'])
            if data[color]['end_ts']:
                end.append(data[color]['end_ts'] / 60)
                curr_all.append(data[color]['end_ts'] / 60)
            else:
                end.append(data[color]['end_ts'])
                curr_all.append(data[color]['end_ts'])
            all.append(curr_all)
            print(curr_all)
        df['color num'] = color_nums
        df['color name'] = color_names
        df['color names conf'] = color_names_conf
        df['starting point (in seconds)'] = start
        df['ending point (in seconds)'] = end
        # print(df)
        return all
        # return df


def add_data_to_sheet(sheet_service, parsed_data):
    body = {
        'values': parsed_data
    }
    res = sheet_service.values().update(spreadsheetId=SPREADSHEET_ID, range="'41'!A1:Z1000",
                                        valueInputOption="USER_ENTERED",
                                        body=body).execute()
    return res


def main(file_name, data_location):
    sa = utils.ServiceAccount(creds, API_SERVICE_NAME, API_VERSION, SCOPES)
    utils.ServiceAccount.Create_Service(sa)
    service = utils.ServiceAccount.get_service_account()
    add_sheet(service, sheet_properties, file_name)  # TODO: check if sheet with this name exists
    data = format_data(data_location)
    sheets_service = service.spreadsheets()
    res = add_data_to_sheet(sheets_service, data)
    return res
