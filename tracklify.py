from __future__ import print_function

import os.path
import base64
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def main():
    subjects = []
    
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

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        
        search_word = "assessment"

        search_query = f"subject:{search_word} OR " \
                       f"body:{search_word} OR " \
                       f"subject:{search_word} OR " \
                       f"body:{search_word} OR "
        
        results = service.users().messages().list(userId='me', q=search_query).execute()
        messages = results.get('messages', [])

        if not messages:
            print(f'No emails containing "{search_word}" found.')
            return
        
        print(f'Emails containing "{search_word}":')
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = msg['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
            
            if subject:
                subjects.append(subject)
                print('Subject:', subject)
            else:
                print('Subject not found for message ID:', message['id'])
                
                
    except HttpError as error:
        # TODO(developer) - Handle errors from Gmail API.
        print(f'An error occurred: {error}')
        
    
    class EmailListWindow(Gtk.Window):
        def __init__(self):
            Gtk.Window.__init__(self, title="Email Subjects")

            self.set_border_width(10)
            self.set_default_size(400, 300)

            # Create a grid layout
            self.grid = Gtk.Grid()
            self.add(self.grid)

            # Add labels and checkboxes for each email subject
            for i, subject in enumerate(subjects):
                label = Gtk.Label(label=subject)
                label.set_alignment(0, 0.5) 
                checkbox = Gtk.CheckButton()
                self.grid.attach(checkbox, 0, i, 1, 1)
                self.grid.attach(label, 1, i, 1, 1)

            # Add a button
            self.button = Gtk.Button(label="Print Selected Subjects")
            self.button.connect("clicked", self.on_button_clicked)
            self.grid.attach(self.button, 0, len(subjects), 2, 1)

        def on_button_clicked(self, widget):
            print("Selected subjects:")
            for i, subject in enumerate(subjects):
                checkbox = self.grid.get_child_at(0, i)
                if checkbox.get_active():
                    print(subject)

    win = EmailListWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()