import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    # Token.json saves your login session, so you don't have to log in every time
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # In your google_calendar.py
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def add_event(summary, start_time_str):
    """
    summary: Headline (i.e. 'Physiotherapist')
    start_time_str: Time in format '2026-02-20T10:00:00'
    """
    service = get_calendar_service()
    
    event = {
        'summary': summary,
        'start': {'dateTime': start_time_str, 'timeZone': 'Europe/Copenhagen'},
        'end': {'dateTime': (datetime.fromisoformat(start_time_str) + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'Europe/Copenhagen'},
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Success: Event '{summary}' created!"
    except Exception as e:
        return f"Error: System could not create the event. {str(e)}"