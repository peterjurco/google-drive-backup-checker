"""
Príklad konfiguračného súboru.
Skopírujte tento súbor ako config.py a upravte hodnoty podľa potreby.
"""

# Adresár pre cache súbory
CACHE_DIR = ".cache"

# Maximálny vek cache v sekundách (3600 = 1 hodina, 86400 = 1 deň)
CACHE_MAX_AGE = 86400

# Veľkosť stránky pre Google Drive API (max 1000)
DRIVE_API_PAGE_SIZE = 1000

# Povoliť paralelné spracovanie (budúca funkcia)
ENABLE_PARALLEL_PROCESSING = False

# Počet pracovných procesov pre paralelné spracovanie
NUM_WORKERS = 4

# Ignorované adresáre pri skenovaní lokálnych súborov
IGNORE_DIRS = [
    '__pycache__',
    '.git',
    '.cache',
    'node_modules',
    '.venv',
    'venv',
]

# Ignorované súbory (pomocou wildcards)
IGNORE_FILES = [
    '.DS_Store',
    'Thumbs.db',
    '*.tmp',
    '*.swp',
]

# Formát výstupného reportu ('json', 'csv', 'html')
OUTPUT_FORMAT = 'json'

# Logovanie
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = None  # None = bez logovania do súboru, alebo 'app.log'

# Google Drive API nastavenia
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Timeout pre API volania (sekundy)
API_TIMEOUT = 300

# Počet opakovaných pokusov pri API chybe
API_RETRY_COUNT = 3

