#!/usr/bin/env python3
"""
Helper skript na zobrazenie Google Drive priečinkov a ich ID.
Pomáha vám nájsť ID priečinka, ktorý chcete porovnať.
"""

import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Autentifikácia s Google Drive."""
    creds = None
    token_path = Path('.cache/token.pickle')
    
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path('credentials.json').exists():
                raise FileNotFoundError(
                    "Súbor 'credentials.json' nebol nájdený. "
                    "Stiahnite ho z Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        token_path.parent.mkdir(exist_ok=True)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def list_folders(show_all=False):
    """
    Zobrazí priečinky na Google Drive.
    
    Args:
        show_all: Ak True, zobrazí všetky priečinky vrátane vnorených.
                  Ak False, zobrazí len priečinky v root (My Drive).
    """
    service = authenticate()
    
    print("\n" + "="*90)
    print("📁 PRIEČINKY NA GOOGLE DRIVE")
    print("="*90)
    
    # Query pre získanie priečinkov
    if show_all:
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        print("(Zobrazujem všetky priečinky vrátane vnorených)")
    else:
        query = "mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
        print("(Zobrazujem len priečinky v My Drive root)")
    
    print()
    print(f"{'Názov priečinka':<50} {'ID priečinka'}")
    print("-" * 90)
    
    try:
        page_token = None
        folder_count = 0
        
        while True:
            results = service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, parents)",
                pageToken=page_token,
                orderBy="name"
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                name = item['name']
                # Skrátime príliš dlhý názov
                if len(name) > 48:
                    name = name[:45] + "..."
                folder_id = item['id']
                print(f"{name:<50} {folder_id}")
                folder_count += 1
            
            page_token = results.get('nextPageToken')
            if not page_token:
                break
        
        print("-" * 90)
        print(f"Celkom nájdených: {folder_count} priečinkov")
        
    except HttpError as error:
        print(f"❌ Chyba API: {error}")
        return
    
    print("\n" + "="*90)
    print("💡 POUŽITIE:")
    print("="*90)
    print("Skopírujte ID priečinka a použite ho s parametrom --drive-folder:")
    print()
    print("  python drive_backup_checker.py /cesta/k/adresaru --drive-folder ID_PRIECINKA")
    print()
    print("Príklad:")
    print("  python drive_backup_checker.py /home/user/documents --drive-folder 1a2b3c4d5e6f...")
    print("="*90 + "\n")

def main():
    """Hlavná funkcia."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Zobrazí Google Drive priečinky a ich ID',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Zobraziť všetky priečinky vrátane vnorených (default: len root priečinky)'
    )
    
    args = parser.parse_args()
    
    try:
        list_folders(show_all=args.all)
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  Prerušené používateľom")
        return 130
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())

