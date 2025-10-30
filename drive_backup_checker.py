#!/usr/bin/env python3
"""
Google Drive Backup Checker
Porovnáva súbory na lokálnom disku s Google Drive.
Optimalizované pre veľké objemy dát.
"""

import os
import json
import pickle
from pathlib import Path
from typing import Dict, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

# Ak meníte rozsah, vymažte token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveBackupChecker:
    def __init__(self, local_root: str, cache_dir: str = ".cache"):
        """
        Inicializácia checkera.
        
        Args:
            local_root: Koreňový adresár lokálnych súborov
            cache_dir: Adresár pre cache súbory
        """
        self.local_root = Path(local_root).resolve()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.service = None
        
    def authenticate(self):
        """Autentifikácia s Google Drive API."""
        creds = None
        token_path = self.cache_dir / 'token.pickle'
        
        # Token sa ukladá do pickle súboru
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Ak nie sú platné credentials, prihlás sa
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
            
            # Ulož credentials pre ďalšie spustenie
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Úspešne pripojené k Google Drive")
    
    def scan_local_files(self, use_cache: bool = True) -> Dict[str, dict]:
        """
        Skenuje lokálne súbory a vytvára index.
        Používa cache pre zrýchlenie pri opakovanom spustení.
        
        Returns:
            Dictionary: {relatívna_cesta: {size, mtime}}
        """
        cache_file = self.cache_dir / 'local_files_cache.json'
        
        if use_cache and cache_file.exists():
            print("Načítavam lokálne súbory z cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        print(f"Skenujem lokálne súbory v: {self.local_root}")
        files_index = {}
        
        # Počítame súbory pre progress bar
        print("Počítam súbory...")
        total_files = sum(1 for _ in self.local_root.rglob('*') if _.is_file())
        
        with tqdm(total=total_files, desc="Skenuje lokálne súbory") as pbar:
            for file_path in self.local_root.rglob('*'):
                if file_path.is_file():
                    try:
                        rel_path = str(file_path.relative_to(self.local_root))
                        stat = file_path.stat()
                        files_index[rel_path] = {
                            'size': stat.st_size,
                            'mtime': stat.st_mtime
                        }
                        pbar.update(1)
                    except (OSError, PermissionError) as e:
                        print(f"Chyba pri čítaní {file_path}: {e}")
        
        # Ulož do cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(files_index, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Nájdených {len(files_index)} lokálnych súborov")
        return files_index
    
    def scan_drive_files(self, folder_id: Optional[str] = None, 
                        use_cache: bool = True) -> Dict[str, dict]:
        """
        Skenuje súbory na Google Drive pomocou API.
        
        Args:
            folder_id: ID priečinka na Drive (None = My Drive root)
            use_cache: Použiť cache
            
        Returns:
            Dictionary: {relatívna_cesta: {id, size, mimeType}}
        """
        cache_file = self.cache_dir / f'drive_files_cache_{folder_id or "root"}.json'
        
        if use_cache and cache_file.exists():
            print("Načítavam Google Drive súbory z cache...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        if not self.service:
            self.authenticate()
        
        if folder_id:
            print(f"Skenujem Google Drive priečinok (ID: {folder_id})...")
            # Overíme, že priečinok existuje a máme k nemu prístup
            try:
                folder_info = self.service.files().get(
                    fileId=folder_id,
                    fields="id, name, mimeType"
                ).execute()
                print(f"✓ Priečinok nájdený: '{folder_info['name']}'")
                
                if folder_info['mimeType'] != 'application/vnd.google-apps.folder':
                    print(f"⚠️  POZOR: Toto nie je priečinok, ale {folder_info['mimeType']}")
            except HttpError as error:
                print(f"❌ Chyba pri prístupe k priečinku: {error}")
                if error.resp.status == 404:
                    print("   Priečinok neexistuje alebo nemáte k nemu prístup.")
                return {}
        else:
            print("Skenujem celý Google Drive (My Drive)...")
        
        files_index = {}
        all_items = []
        
        # Rekurzívna funkcia na získanie všetkých súborov z priečinka
        def get_files_recursive(parent_id: Optional[str]):
            """Rekurzívne získa všetky súbory z priečinka a podpriečinkov."""
            # Query pre získanie položiek z priečinka
            if parent_id:
                query = f"'{parent_id}' in parents and trashed=false"
            else:
                query = "trashed=false"
            
            page_token = None
            items = []
            
            while True:
                try:
                    results = self.service.files().list(
                        pageSize=1000,
                        fields="nextPageToken, files(id, name, mimeType, size, parents)",
                        pageToken=page_token,
                        q=query
                    ).execute()
                    
                    page_items = results.get('files', [])
                    items.extend(page_items)
                    page_token = results.get('nextPageToken')
                    
                    if not page_token:
                        break
                        
                except HttpError as error:
                    print(f"❌ Chyba API: {error}")
                    break
            
            return items
        
        # Získame všetky súbory (ak folder_id, len z toho priečinka, inak všetko)
        print("Načítavam zoznam súborov z Drive...")
        
        if folder_id:
            # Najprv získame obsah špecifického priečinka
            direct_items = get_files_recursive(folder_id)
            print(f"  Priamo v priečinku: {len(direct_items)} položiek")
            
            # Počítadlá pre debugging
            folders_to_scan = []
            files_count = 0
            folders_count = 0
            
            for item in direct_items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    folders_to_scan.append(item)
                    folders_count += 1
                else:
                    files_count += 1
            
            print(f"    → {files_count} súborov")
            print(f"    → {folders_count} podpriečinkov")
            
            all_items.extend(direct_items)
            
            # Rekurzívne prejdeme všetky podpriečinky
            if folders_to_scan:
                print(f"  Skenujem {len(folders_to_scan)} podpriečinkov...")
                scanned_count = 0
                
                while folders_to_scan:
                    folder = folders_to_scan.pop(0)
                    scanned_count += 1
                    sub_items = get_files_recursive(folder['id'])
                    
                    if sub_items:
                        print(f"    [{scanned_count}/{scanned_count + len(folders_to_scan)}] '{folder['name']}': {len(sub_items)} položiek")
                    
                    for item in sub_items:
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            folders_to_scan.append(item)
                    
                    all_items.extend(sub_items)
            
            files_to_process = all_items
        else:
            # Skenujeme celý Drive
            files_to_process = get_files_recursive(None)
        
        print(f"\nCelkom načítaných {len(files_to_process)} položiek z Drive")
        
        # Vytvoríme mapu ID -> item pre rýchle vyhľadávanie
        id_to_item = {item['id']: item for item in files_to_process}
        
        # Funkcia na rekonštrukciu cesty
        def get_relative_path(item, root_id):
            """
            Vytvorí relatívnu cestu k súboru.
            Ak je root_id zadaný, cesta je relatívna k tomuto priečinku.
            """
            path_parts = [item['name']]
            current_parents = item.get('parents', [])
            
            # Ideme nahor hierarchiou až po root_id (alebo úplný root)
            while current_parents:
                parent_id = current_parents[0]
                
                # Ak sme dosiahli root priečinok, zastavíme
                if root_id and parent_id == root_id:
                    break
                
                # Ak rodič je v našom indexe
                if parent_id in id_to_item:
                    parent_item = id_to_item[parent_id]
                    path_parts.insert(0, parent_item['name'])
                    current_parents = parent_item.get('parents', [])
                else:
                    # Rodič nie je v indexe (je mimo skenovej oblasti)
                    break
            
            return '/'.join(path_parts)
        
        # Spracovanie súborov (nie priečinkov)
        print("\nSpracovávam cesty súborov...")
        
        # Počítadlá pre štatistiku
        skipped_folders = 0
        skipped_google_docs = 0
        processed_files = 0
        
        with tqdm(total=len(files_to_process), desc="Vytváram index") as pbar:
            for item in files_to_process:
                # Preskočíme priečinky
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    skipped_folders += 1
                    pbar.update(1)
                    continue
                
                # Preskočíme Google-native dokumenty (Docs, Sheets, atď.)
                if item['mimeType'].startswith('application/vnd.google-apps.'):
                    skipped_google_docs += 1
                    pbar.update(1)
                    continue
                
                # Vytvoríme relatívnu cestu
                rel_path = get_relative_path(item, folder_id)
                
                files_index[rel_path] = {
                    'id': item['id'],
                    'size': int(item.get('size', 0)),
                    'mimeType': item['mimeType']
                }
                processed_files += 1
                pbar.update(1)
        
        # Štatistika
        print(f"\n📊 Štatistika skenovania:")
        print(f"  Súbory spracované:     {processed_files}")
        print(f"  Priečinky preskočené:  {skipped_folders}")
        print(f"  Google Docs preskočené: {skipped_google_docs}")
        
        if skipped_google_docs > 0:
            print(f"\n💡 TIP: Google Docs/Sheets/Slides nemajú 'size' a nedajú sa priamo porovnať.")
            print(f"         Tieto súbory sú preskočené (celkom {skipped_google_docs}).")
        
        # Ulož do cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(files_index, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Nájdených {len(files_index)} súborov na Drive")
        return files_index
    
    def compare_files(self, local_files: Dict, drive_files: Dict) -> Dict:
        """
        Porovná lokálne súbory s Drive súbormi.
        
        Returns:
            Dictionary s výsledkami porovnania
        """
        print("\nPorovnávam súbory...")
        
        local_paths = set(local_files.keys())
        drive_paths = set(drive_files.keys())
        
        # Súbory iba lokálne (chýbajú na Drive)
        only_local = local_paths - drive_paths
        
        # Súbory iba na Drive (chýbajú lokálne)
        only_drive = drive_paths - local_paths
        
        # Súbory v oboch umiestneniach
        in_both = local_paths & drive_paths
        
        # Kontrola veľkosti pre súbory v oboch umiestneniach
        size_mismatch = []
        for path in in_both:
            local_size = local_files[path]['size']
            drive_size = drive_files[path]['size']
            if local_size != drive_size:
                size_mismatch.append({
                    'path': path,
                    'local_size': local_size,
                    'drive_size': drive_size
                })
        
        return {
            'only_local': sorted(only_local),
            'only_drive': sorted(only_drive),
            'in_both': sorted(in_both),
            'size_mismatch': size_mismatch,
            'total_local': len(local_files),
            'total_drive': len(drive_files)
        }
    
    def print_report(self, results: Dict):
        """Vytlačí prehľadnú správu o porovnaní."""
        print("\n" + "="*70)
        print("VÝSLEDKY POROVNANIA")
        print("="*70)
        
        print(f"\n📊 ŠTATISTIKA:")
        print(f"  Lokálne súbory:    {results['total_local']:>10,}")
        print(f"  Drive súbory:      {results['total_drive']:>10,}")
        print(f"  V oboch:           {len(results['in_both']):>10,}")
        
        print(f"\n⚠️  ROZDIELY:")
        print(f"  Iba lokálne:       {len(results['only_local']):>10,}")
        print(f"  Iba na Drive:      {len(results['only_drive']):>10,}")
        print(f"  Rozdiel veľkosti:  {len(results['size_mismatch']):>10,}")
        
        # Detail - súbory iba lokálne
        if results['only_local']:
            print(f"\n📁 SÚBORY IBA LOKÁLNE (prvých 20):")
            for path in results['only_local'][:20]:
                print(f"  - {path}")
            if len(results['only_local']) > 20:
                print(f"  ... a ďalších {len(results['only_local']) - 20}")
        
        # Detail - súbory iba na Drive
        if results['only_drive']:
            print(f"\n☁️  SÚBORY IBA NA DRIVE (prvých 20):")
            for path in results['only_drive'][:20]:
                print(f"  - {path}")
            if len(results['only_drive']) > 20:
                print(f"  ... a ďalších {len(results['only_drive']) - 20}")
        
        # Detail - rozdielne veľkosti
        if results['size_mismatch']:
            print(f"\n⚖️  ROZDIELNE VEĽKOSTI (prvých 10):")
            for item in results['size_mismatch'][:10]:
                print(f"  - {item['path']}")
                print(f"    Lokálne: {item['local_size']:>15,} B")
                print(f"    Drive:   {item['drive_size']:>15,} B")
            if len(results['size_mismatch']) > 10:
                print(f"  ... a ďalších {len(results['size_mismatch']) - 10}")
        
        print("\n" + "="*70)
    
    def save_detailed_report(self, results: Dict, output_file: str = "report.json"):
        """Uloží detailnú správu do JSON súboru."""
        output_path = self.cache_dir / output_file
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'local_root': str(self.local_root),
            'statistics': {
                'total_local': results['total_local'],
                'total_drive': results['total_drive'],
                'in_both': len(results['in_both']),
                'only_local': len(results['only_local']),
                'only_drive': len(results['only_drive']),
                'size_mismatch': len(results['size_mismatch'])
            },
            'details': {
                'only_local': results['only_local'],
                'only_drive': results['only_drive'],
                'size_mismatch': results['size_mismatch']
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Detailná správa uložená do: {output_path}")
    
    def clear_cache(self):
        """Vymaže cache súbory."""
        for cache_file in self.cache_dir.glob('*_cache.json'):
            cache_file.unlink()
        print("✓ Cache vymazaná")


def main():
    """Hlavná funkcia."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Porovnanie lokálnych súborov s Google Drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Príklady použitia:
  %(prog)s /home/user/data
  %(prog)s /home/user/data --no-cache
  %(prog)s /home/user/data --clear-cache
        """
    )
    
    parser.add_argument(
        'local_path',
        help='Cesta k lokálnemu adresáru na porovnanie'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Nespustiť skenovaní odznova bez použitia cache'
    )
    
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Vymazať cache pred spustením'
    )
    
    parser.add_argument(
        '--drive-folder',
        help='ID priečinka na Google Drive (nepovinné)'
    )
    
    parser.add_argument(
        '--output',
        default='report.json',
        help='Názov výstupného súboru so správou (default: report.json)'
    )
    
    args = parser.parse_args()
    
    # Validácia lokálnej cesty
    if not os.path.exists(args.local_path):
        print(f"❌ Chyba: Cesta neexistuje: {args.local_path}")
        return 1
    
    if not os.path.isdir(args.local_path):
        print(f"❌ Chyba: Cesta nie je adresár: {args.local_path}")
        return 1
    
    # Vytvorenie checkera
    checker = DriveBackupChecker(args.local_path)
    
    # Vymazanie cache ak je požadované
    if args.clear_cache:
        checker.clear_cache()
    
    use_cache = not args.no_cache
    
    try:
        # Autentifikácia
        checker.authenticate()
        
        # Skenovanie lokálnych súborov
        local_files = checker.scan_local_files(use_cache=use_cache)
        
        # Skenovanie Drive súborov
        drive_files = checker.scan_drive_files(
            folder_id=args.drive_folder,
            use_cache=use_cache
        )
        
        # Porovnanie
        results = checker.compare_files(local_files, drive_files)
        
        # Výstup
        checker.print_report(results)
        checker.save_detailed_report(results, args.output)
        
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

