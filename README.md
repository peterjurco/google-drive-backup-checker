# Google Drive Backup Checker

Python skript na porovnanie lokálnych súborov s Google Drive. Optimalizovaný pre veľké objemy dát (aj terabajty).

## ✨ Funkcie

- 🔍 Porovnanie lokálnych súborov s Google Drive
- ⚡ Optimalizované pre veľké objemy dát
- 💾 Cache systém pre rýchlejšie opakované spustenia
- 📊 Detailné reporty v JSON formáte
- 🎯 Kontrola prítomnosti súborov v oboch úložiskách
- ⚖️ Kontrola veľkosti súborov
- 📈 Progress bar pre sledovanie priebehu

## 📋 Požiadavky

- Python 3.7+
- Google Cloud Project s povoleným Google Drive API
- Prístup k internetu

## 🚀 Inštalácia

### 1. Naklonujte/vytvorte projekt

```bash
cd google-drive-backup-checker
```

### 2. Vytvorte virtuálne prostredie (odporúčané)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# alebo
venv\Scripts\activate  # Windows
```

### 3. Nainštalujte závislosti

```bash
pip install -r requirements.txt
```

### 4. Nastavte Google Drive API

#### a) Vytvorte projekt v Google Cloud Console

1. Prejdite na [Google Cloud Console](https://console.cloud.google.com/)
2. Vytvorte nový projekt alebo vyberte existujúci
3. Povoľte **Google Drive API**:
   - V navigácii prejdite na "APIs & Services" > "Library"
   - Vyhľadajte "Google Drive API"
   - Kliknite na "Enable"

#### b) Vytvorte OAuth 2.0 credentials

1. V navigácii prejdite na "APIs & Services" > "Credentials"
2. Kliknite na "Create Credentials" > "OAuth client ID"
3. Ak je potrebné, nakonfigurujte "OAuth consent screen":
   - Vyberte "External" (alebo "Internal" ak máte Google Workspace)
   - Vyplňte potrebné informácie
   - Pridajte scope: `.../auth/drive.readonly`
   - Pridajte testovacích používateľov (ak je External)
4. Vytvorte OAuth client ID:
   - Application type: **Desktop app**
   - Dajte mu názov (napr. "Drive Backup Checker")
5. Stiahnite JSON súbor s credentials
6. Premenujte ho na `credentials.json` a umiestnite ho do tohto adresára

## 📖 Použitie

### Základné použitie

```bash
python drive_backup_checker.py /cesta/k/lokalnym/suborom
```

### Príklady

```bash
# Porovnať adresár /home/user/documents
python drive_backup_checker.py /home/user/documents

# Vynútiť nové skenovanie bez použitia cache
python drive_backup_checker.py /home/user/documents --no-cache

# Vymazať cache pred spustením
python drive_backup_checker.py /home/user/documents --clear-cache

# Vlastný názov výstupného súboru
python drive_backup_checker.py /home/user/documents --output moja-sprava.json
```

### Parametre

- `local_path` - **Povinný**. Cesta k lokálnemu adresáru na porovnanie
- `--no-cache` - Vynútiť nové skenovanie bez použitia cache
- `--clear-cache` - Vymazať cache pred spustením
- `--drive-folder ID` - ID špecifického priečinka na Google Drive (voliteľné)
- `--output FILENAME` - Názov výstupného JSON súboru (default: `report.json`)

## 🔍 Ako získať ID priečinka na Google Drive

Ak chcete porovnať len konkrétny priečinok na Drive (nie celý Drive), potrebujete jeho ID:

### Metóda 1: Z URL v prehliadači (najjednoduchšie)

1. Otvorte [Google Drive](https://drive.google.com) v prehliadači
2. Otvorte priečinok, ktorý chcete porovnať
3. Pozrite sa na URL v adresnom riadku:

```
https://drive.google.com/drive/folders/1XyZ_aBcDeFgHiJkLmNoPqRsTuVwXyZ123
                                         └────────────────────────────┘
                                              Toto je ID priečinka!
```

4. Skopírujte dlhý reťazec za `/folders/`

### Metóda 2: Cez "Share" tlačidlo

1. Kliknite pravým tlačidlom na priečinok v Google Drive
2. Vyberte **"Share"** alebo **"Get link"**
3. Skopírujte link - ID je v ňom medzi `/folders/` a `?`:

```
https://drive.google.com/drive/folders/1XyZ_aBcDeFgHiJkLmNoPqRsTuVwXyZ123?usp=sharing
                                         └────────────────────────────┘
```

### Metóda 3: Pomocou helper skriptu

Použite priložený helper skript, ktorý vypíše všetky priečinky s ID:

```bash
# Zobraziť priečinky v My Drive root
python list_drive_folders.py

# Zobraziť všetky priečinky vrátane vnorených
python list_drive_folders.py --all
```

Výstup:
```
📁 PRIEČINKY NA GOOGLE DRIVE
==========================================================================================
Názov priečinka                                    ID priečinka
------------------------------------------------------------------------------------------
Dokumenty                                          1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
Fotky                                              9i8h7g6f5e4d3c2b1a0z9y8x7w6v5u4t
Zálohy 2024                                        1XyZ_aBcDeFgHiJkLmNoPqRsTuVwXyZ123
------------------------------------------------------------------------------------------
```

### Použitie ID

```bash
# Porovnať lokálny adresár so špecifickým priečinkom na Drive
python drive_backup_checker.py /home/user/documents \
    --drive-folder 1XyZ_aBcDeFgHiJkLmNoPqRsTuVwXyZ123

# Príklad pre priečinok "Zálohy 2024"
python drive_backup_checker.py /mnt/e/Backup \
    --drive-folder 1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

**Poznámka:** 
- **Bez** `--drive-folder` → porovná s celým "My Drive"
- **S** `--drive-folder ID` → porovná len s obsahom zadaného priečinka (vrátane podpriečinkov)

## 🎯 Prvé spustenie

Pri prvom spustení:

1. Otvorí sa webový prehliadač
2. Prihláste sa do Google účtu
3. Povolte prístup k Drive (read-only)
4. Po úspešnej autentifikácii sa vytvorí `token.pickle` v `.cache/` adresári
5. Pri ďalších spusteniach už nebude potrebné znovu sa prihlasovať

## 📊 Výstup

Skript vytvorí:

### Konzolový výstup

```
VÝSLEDKY POROVNANIA
====================================================================

📊 ŠTATISTIKA:
  Lokálne súbory:          1,523
  Drive súbory:            1,489
  V oboch:                 1,450

⚠️  ROZDIELY:
  Iba lokálne:                73
  Iba na Drive:               39
  Rozdiel veľkosti:           12

📁 SÚBORY IBA LOKÁLNE (prvých 20):
  - documents/new_file.pdf
  - photos/2024/IMG_5678.jpg
  ...
```

### JSON Report

Detailná správa v `.cache/report.json`:

```json
{
  "timestamp": "2024-10-30T10:30:00",
  "local_root": "/home/user/documents",
  "statistics": {
    "total_local": 1523,
    "total_drive": 1489,
    "in_both": 1450,
    "only_local": 73,
    "only_drive": 39,
    "size_mismatch": 12
  },
  "details": {
    "only_local": [...],
    "only_drive": [...],
    "size_mismatch": [...]
  }
}
```

## ⚡ Optimalizácie

Skript je optimalizovaný pre veľké objemy dát:

1. **Cache systém**: Ukladá výsledky skenovania, aby nebolo potrebné skenova znovu
2. **Paginácia**: Google Drive API volania používajú maximálnu veľkosť stránky (1000)
3. **Efektívne dátové štruktúry**: Používa sets a dictionaries pre rýchle porovnávanie
4. **Progress bary**: Vizuálna indikácia priebehu pomocou `tqdm`
5. **Lazy loading**: Spracováva súbory postupne, nie všetky naraz v pamäti

## 🗂️ Štruktúra projektu

```
google-drive-backup-checker/
├── drive_backup_checker.py    # Hlavný skript
├── list_drive_folders.py      # Helper pre zoznam priečinkov a ID
├── requirements.txt            # Python závislosti
├── config.example.py           # Príklad konfigurácie
├── credentials.json            # Google API credentials (pridáte vy)
├── .gitignore                  # Git ignore pravidlá
├── README.md                   # Tento súbor
└── .cache/                     # Automaticky vytvorený
    ├── token.pickle                   # Autentifikačný token
    ├── local_files_cache.json         # Cache lokálnych súborov
    ├── drive_files_cache_root.json    # Cache Drive súborov (celý Drive)
    ├── drive_files_cache_ID.json      # Cache pre konkrétny priečinok
    └── report.json                    # Výsledný report
```

## 🔒 Bezpečnosť

- Skript požaduje **iba read-only** prístup k Drive (`drive.readonly` scope)
- `credentials.json` a `token.pickle` obsahujú citlivé dáta - **nikdy ich necommitujte** do git
- Pridajte do `.gitignore`:
  ```
  credentials.json
  .cache/
  venv/
  ```

## ❓ Riešenie problémov

### "credentials.json not found"

Potrebujete vytvoriť OAuth credentials v Google Cloud Console a stiahnuť JSON súbor.

### "Access denied" alebo "Insufficient permissions"

Uistite sa, že OAuth consent screen má správne nastavené scopes a ste pridaný ako testovací používateľ.

### Skript je pomalý

- Pri prvom spustení je normálne, že trvá dlhšie (skenuje všetky súbory)
- Pri ďalších spusteniach použije cache (výrazne rýchlejšie)
- Pre nové skenovanie použite `--clear-cache`

### "Token expired"

Vymažte `token.pickle` a znovu sa prihláste:
```bash
rm .cache/token.pickle
python drive_backup_checker.py /cesta/k/adresaru
```

## 🔄 Budúce vylepšenia

Možné rozšírenia v budúcich verziách:

- ✅ Kontrola prítomnosti súborov (implementované)
- ✅ Kontrola veľkosti súborov (implementované)
- ⬜ Kontrola hash/checksum súborov (MD5)
- ⬜ Paralelné skenovanie lokálnych súborov
- ⬜ Automatická synchronizácia chýbajúcich súborov
- ⬜ Web UI dashboard
- ⬜ Plánovanie pravidelných kontrol (cron job)
- ⬜ E-mail notifikácie pri rozdieloch

## 📝 Licencia

MIT License - voľne použiteľné

## 👨‍💻 Autor

Vytvorené pre efektívnu správu záloh medzi lokálnym úložiskom a Google Drive.

