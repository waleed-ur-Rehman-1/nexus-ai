import os
import pickle
import re
from datetime import datetime, timedelta
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from agents.base_agent import BaseAgent

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarAgent(BaseAgent):
    name = "calendar_agent"

    def __init__(self):
        self.creds = None
        self.service = None
        self.token_file = 'token.pickle'
        self.credentials_file = 'credentials.json'
        self._authenticate()

    def _authenticate(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Missing {self.credentials_file}. Please download OAuth credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("✅ Google Calendar authenticated")

    # ---------- Core Methods ----------
    def get_events(self, days=1, max_results=10):
        if not self.service:
            return {"success": False, "message": "Not authenticated."}
        now = datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return {"success": True, "message": "No upcoming events found.", "events": []}
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted_events.append({
                'summary': event.get('summary', 'No title'),
                'start': start,
                'end': end,
                'description': event.get('description', ''),
                'id': event['id']
            })
        return {
            "success": True,
            "agent": self.name,
            "action": "get_events",
            "count": len(formatted_events),
            "events": formatted_events
        }

    def add_event(self, summary, start_time, end_time, description=""):
        if not self.service:
            return {"success": False, "message": "Not authenticated."}
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'Asia/Karachi',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'Asia/Karachi',
            },
        }
        created_event = self.service.events().insert(calendarId='primary', body=event).execute()
        return {
            "success": True,
            "agent": self.name,
            "action": "add_event",
            "event": {
                "id": created_event['id'],
                "summary": created_event['summary'],
                "start": created_event['start'].get('dateTime'),
                "end": created_event['end'].get('dateTime')
            },
            "message": f"Event '{summary}' created successfully."
        }

    def delete_event(self, event_id):
        if not self.service:
            return {"success": False, "message": "Not authenticated."}
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        return {"success": True, "agent": self.name, "action": "delete_event", "message": "Event deleted."}

    # ---------- Natural Language Parsing for Add Event ----------
    def parse_add_event_command(self, command: str) -> dict:
        """
        Extract event details from natural language.
        Returns dict with summary, start_time, end_time, description.
        """
        cmd = command.lower()
        # Extract title (everything before "at", "on", "tomorrow", etc.)
        title_match = re.search(r'(?:add|schedule|create)\s+(?:a|an|meeting|event|appointment)?\s*([^.]+?)(?:\s+at\s+|\s+on\s+|\s+tomorrow|\s+next|\s+this|\s*$)', command, re.IGNORECASE)
        summary = title_match.group(1).strip() if title_match else "Untitled Event"

        # Extract time (e.g., "3 PM", "10:00", "15:30")
        time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm|a\.m\.|p\.m\.))', command)
        time_str = time_match.group(1) if time_match else "12:00 PM"
        try:
            parsed_time = datetime.strptime(time_str.strip(), "%I:%M %p")
            hour = parsed_time.hour
            minute = parsed_time.minute
        except:
            try:
                parsed_time = datetime.strptime(time_str.strip(), "%I%p")
                hour = parsed_time.hour
                minute = 0
            except:
                hour = 12
                minute = 0

        # Determine date
        now = datetime.now()
        if "tomorrow" in cmd:
            date = now + timedelta(days=1)
        elif "next" in cmd:
            date = now + timedelta(days=7)
        elif "friday" in cmd:
            days_ahead = 4 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            date = now + timedelta(days=days_ahead)
        else:
            date = now

        start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        tz = pytz.timezone('Asia/Karachi')
        start_time = tz.localize(start_time)
        end_time = tz.localize(end_time)

        return {
            "summary": summary,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "description": command
        }

    # ---------- Execute ----------
    def execute(self, command: str) -> dict:
        cmd = command.lower().strip()

        if "schedule" in cmd or "events" in cmd or "calendar" in cmd:
            if "today" in cmd:
                days = 1
            elif "tomorrow" in cmd:
                days = 2
            elif "week" in cmd:
                days = 7
            else:
                days = 1
            return self.get_events(days=days)

        elif "add" in cmd and ("meeting" in cmd or "event" in cmd or "appointment" in cmd or "schedule" in cmd):
            parsed = self.parse_add_event_command(command)
            return self.add_event(parsed["summary"], parsed["start_time"], parsed["end_time"], parsed["description"])

        else:
            return {"success": False, "agent": self.name, "message": "Calendar Agent: Command not understood."}