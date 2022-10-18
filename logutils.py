import re
from datetime import datetime as dt, date as date_dt
import os.path
from config import *

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

KEYS = ['Starting Time', 'Target', 'Filter', 'Binning', 'Gain', 'Exp. Time (s)', '# of Exp.', 'Camera Temp.', 'Capture Software', 'Capture Setup', 'Note']

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

def fromDateRow(s):
    return {'Date': dt.strptime(re.search(r'^\d+', s).group(0), "%Y%m%d").date(),
            'Observer': re.search(r', Observer: (.+)$', s).group(1)}

def toDateRow(date, name):
    return "{}, Observer: {}".format(date_dt.strftime(date, "%Y%m%d"), name)

def toLogRow(obs):
    return [obs[k] for k in filter(lambda x: x in obs, KEYS)]

def readLog(sheetName = None, date = None, target_date_only=True):
    if date is None:
        date = date_dt.today()
    if sheetName is None:
        if type(date) != date_dt:
            date = dt.strptime(re.search(r'^\d+', str(date)).group(0), "%Y%m%d").date()
        month = int(date.strftime("%m"))

        if 1 <= month <= 4:
            sheetName = "January~April"
        elif 5 <= month <= 8:
            sheetName = "May~August"
        elif 9 <= month <= 12:
            sheetName = "September~December"

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    val = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"'{sheetName}'!A2:Z").execute().get('values')

    observations = []
    for r in val:
        if len(r) == 1:
            meta = fromDateRow(r[0])
            continue
        r += (len(KEYS)-len(r))*['']
        observations.append(meta|{KEYS[i]:x for i, x in enumerate(r)})

    if target_date_only:
        observations = list(filter(lambda x: x['Date'] == date, observations))

    return observations

def appendObs(obs, sheetName = None):
    date = obs['Date']
    if sheetName is None:
        if type(date) != date_dt:
            date = dt.strptime(re.search(r'^\d+', str(date)).group(0), "%Y%m%d").date()
        month = int(date.strftime("%m"))

        if 1 <= month <= 4:
            sheetName = "January~April"
        elif 5 <= month <= 8:
            sheetName = "May~August"
        elif 9 <= month <= 12:
            sheetName = "September~December"

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    return sheet.values().append(spreadsheetId=SPREADSHEET_ID, range=f"'{sheetName}'!A2:Z",
                                 valueInputOption="USER_ENTERED",
                                 body={'values': [toLogRow(obs)]}).execute()

def appendDateRow(date = None, name = '', sheetName = None):
    if date is None:
        date = date_dt.today()
    if sheetName is None:
        if type(date) != date_dt:
            date = dt.strptime(re.search(r'^\d+', str(date)).group(0), "%Y%m%d").date()
        month = int(date.strftime("%m"))

        if 1 <= month <= 4:
            sheetName = "January~April"
        elif 5 <= month <= 8:
            sheetName = "May~August"
        elif 9 <= month <= 12:
            sheetName = "September~December"

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    sheets = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()['sheets']
    sid = list(filter(lambda x: x['properties']['title'] == sheetName, sheets))[0]['properties']['sheetId']

    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"'{sheetName}'!A:Z").execute()
    last_row = len(result.get('values'))

    return sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID,
                             body={'requests': [{'mergeCells': {
                                   'range': {'sheetId': sid,
                                             'startRowIndex': last_row,
                                             'endRowIndex': last_row+1,
                                             'startColumnIndex': 0,
                                             'endColumnIndex': 25},
                                   'mergeType': 'MERGE_ROWS'
                                   }},
                                                {"updateCells": {
                                                 "rows": [
                                                      {"values": [{"userEnteredValue":
                                                                   {'stringValue': toDateRow(date, name)},
                                                                   "userEnteredFormat":
                                                                   {"backgroundColor": {"red": 200/255,
                                                                                        "green": 218/255,
                                                                                        "blue": 249/255,
                                                                                        "alpha": 1}}
                                                                   }]}
                                                  ],
                                                 "fields": 'userEnteredValue, userEnteredFormat.backgroundColor',
                                                 "range": {"sheetId": sid,
                                                           "startRowIndex": last_row,
                                                           "endRowIndex": last_row+1,
                                                           "startColumnIndex": 0,
                                                           "endColumnIndex": 1}
                                   }}]}).execute()

def newObs(obs):
    observations = readLog(date=obs['Date'], target_date_only=False)
    if len(observations) and ((observations[-1]['Date'], observations[-1]['Observer']) 
                              == (obs['Date'], obs['Observer'])):
        appendObs(obs)
    else:
        appendDateRow(date = obs['Date'], name = obs['Observer'])
        appendObs(obs)

