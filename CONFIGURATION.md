"""
Configuration Guide für Financial Cockpit.
Erklärt alle anpassbaren Parameter.
"""

# ============================================================
# OLLAMA KONFIGURATION
# ============================================================

# Datei: llm_extractor.py, Zeile ~20-22

OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama Server URL
OLLAMA_MODEL = "llama3"                      # Modell: llama3, mistral, neural-chat

# Modelle zum Download:
# ollama pull llama3        # Empfohlen, 4GB
# ollama pull mistral       # Schneller, 3GB  
# ollama pull neural-chat   # Mittelmäßig, 3GB
# ollama pull orca2         # Sehr genau, 5GB


# ============================================================
# LLM PARAMETER (in call_ollama_api)
# ============================================================

"""
"temperature": 0.3       # Niedrig = präzise, Hoch = kreativ
"stream": False          # Nicht streamen, nur fertige Antwort
"timeout": 60            # Sekunden bis Timeout
"""

# Empfohlene Werte:
# - Finanzanalyse: 0.2-0.3 (sehr präzise)
# - Flexibel: 0.5 (Standard)
# - Kreativ: 0.7-0.9 (experimentel)


# ============================================================
# TEXT CHUNKING (in chunk_text)
# ============================================================

chunk_size = 3000       # Zeichen pro Chunk
overlap = 300           # Überlappung zwischen Chunks

# Szenarios:
# - Kurze Docs: 2000 / 100
# - Normal: 3000 / 300
# - Lange Docs: 5000 / 500
# - Sehr genau: 2000 / 500


# ============================================================
# LOGGING LEVEL
# ============================================================

# Datei: app.py (oben anpassen)

import logging

logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Levels:
# - DEBUG: Sehr detailliert (nur für Troubleshooting)
# - INFO: Normal (Standard)
# - WARNING: Nur Warnungen
# - ERROR: Nur Fehler


# ============================================================
# STREAMLIT KONFIGURATION
# ============================================================

# Datei: ~/.streamlit/config.toml (optional)

"""
[client]
showErrorDetails = true
logger.level = "debug"

[server]
port = 8501
headless = true
maxUploadSize = 200  # MB

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
"""


# ============================================================
# FIREWALL / NETZWERK
# ============================================================

# Falls Ollama auf anderem Host:

OLLAMA_BASE_URL = "http://192.168.1.100:11434"  # Remote Ollama
# Achtung: Weniger sicher, nur im Local Network!


# ============================================================
# UMGEBUNGSVARIABLEN (.env)
# ============================================================

"""
# .env Datei erstellen und nutzen mit:
from dotenv import load_dotenv
import os

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
"""


# ============================================================
# PDF VERARBEITUNG
# ============================================================

# Datei: pdf_parser.py

# Fallback bei gescannten PDFs (OCR):
# Aktuell NICHT unterstützt
# Nutze: https://github.com/jbarlow83/OCRmyPDF

# Alternative mit pytesseract:
# pip install pytesseract pillow
# brew install tesseract


# ============================================================
# DATENSPEICHERUNG
# ============================================================

# Standardmäßig in:
# - /data/  → JSON Ergebnisse
# - /uploads/  → Hochgeladene PDFs

# Custom Pfade (in app.py):
UPLOAD_DIR = Path("my_pdfs")        # Andere Upload dir
DATA_DIR = Path("my_results")       # Andere Results dir


# ============================================================
# PERFORMANCE TUNING
# ============================================================

# Für schnellere Extraktion:

# 1. Kleinere Chunks
chunk_size = 2000  # von 3000
overlap = 100      # von 300

# 2. Schnelleres Modell
OLLAMA_MODEL = "mistral"  # statt llama3

# 3. Höhere Temperatur (weniger präzise aber schneller)
"temperature": 0.7  # von 0.3

# 4. Weniger Retries
max_retries = 1  # von 3 in call_ollama_api


# ============================================================
# MEMORY/RESSOURCEN
# ============================================================

# Pro Modell (rough estimates):
# - llama3: 4GB RAM, Apple Silicon bevorzugt
# - mistral: 3.5GB RAM
# - neural-chat: 3GB RAM
# - orca2: 5GB RAM

# Bei Speichermangel:
# 1. Kleinere Chunks verwenden
# 2. Schneller Modell (mistral)
# 3. Ollama mit weniger RAM starten:
#    OLLAMA_NUM_GPU=0 ollama serve  (CPU only)


# ============================================================
# FEHLERBEHANDLUNG
# ============================================================

# Timeout erhöhen (lange PDFs):
response = requests.post(
    ...,
    timeout=120  # von 60 Sekunden
)

# Retry retry logic:
max_retries = 5  # von 3

# Custom Error Handling:
try:
    results = extract_financials(text)
except TimeoutError:
    # Fallback
    results = {}


# ============================================================
# API CALLS LIMIT
# ============================================================

# Ollama hat kein hardwarelimit, aber:
time.sleep(0.5)  # Rate limiting zwischen Chunks


# ============================================================
# EXPORT FORMATE
# ============================================================

# JSON (Standard)
export_json()

# CSV (Custom, schreibe selbst):
import csv
with open('results.csv', 'w') as f:
    writer = csv.writer(f)
    # ...

# EXCEL
# pip install openpyxl
import openpyxl
# ...


# ============================================================
# SICHERHEIT
# ============================================================

# Alle Operationen sind lokal, aber:
# 1. PDFs können nicht gelöscht werden nach Upload
#    → Benutzer muss selbst /uploads leeren
# 2. Keine Authentifizierung in Streamlit
#    → Nur verwenden hinter Firewall/VPN
# 3. Datenspeicherung:
#    → /data enthält extrahierte Finanzdaten


# ============================================================
# TIPPS FÜR BESTE ERGEBNISSE
# ============================================================

"""
1. PDF-Qualität
   - Hochauflösend (nicht gescannt)
   - Deutsch oder Englisch
   - Modernes Layout (nicht 1990er)

2. LLM-Prompt
   - Sehr spezifisch für deutsche Begriffe
   - Erwarte JSON-Output
   - Nutze Kontext-Snippets

3. Chunk-Strategie
   - Zu kleine Chunks: Verlust von Kontext
   - Zu große Chunks: Langsamer, mehr RAM
   - Überlappung: Hilft bei Sentenzen über Grenzen

4. Monitoring
   - Logs checken: logging.basicConfig(level=DEBUG)
   - Test mit test_suite.py
   - Vergleiche Ergebnisse


Große Unternehmen (>100MB PDF):
- Split in mehrere PDFs
- Batch-Prozesses mit examples.py
"""


# ============================================================
# TROUBLESHOOTING CHECKLISTE
# ============================================================

"""
Problem: "ModuleNotFoundError: No module named 'streamlit'"
→ pip install -r requirements.txt

Problem: "Ollama nicht erreichbar"
→ ps aux | grep ollama
→ ollama serve

Problem: "Timeout bei Ollama API"
→ timeout erhöhen in llm_extractor.py
→ kleinere chunks verwenden

Problem: "JSON Parse Fehler"
→ LLM gibt kein gültiges JSON zurück
→ Temperature reduzieren (0.2)

Problem: "Keine Werte extrahiert"
→ PDF-Format überprüfen (gescannt?)
→ Deutsche Begriffe im Prompt anpassen
→ logs mit DEBUG level anschauen

Problem: "App sehr langsam"
→ Schneller Modell verwenden (mistral)
→ Größere chunks
→ Weniger retries

Problem: "Speicherplatz voll"
→ /uploads aufräumen
→ /data archivieren
"""


# ============================================================
# BACKUPS & ARCHIVIERUNG
# ============================================================

"""
Regelmäßig sichern:
- /data/*.json → Google Drive / AWS S3
- /uploads/*.pdf → Archive

Langfristige Speicherung:
- JSON → Datenbank (optional)
- PDF → Cold storage
"""


if __name__ == "__main__":
    print("""
    📋 Configuration Guide für Financial Cockpit
    
    Siehe den Quellcode für alle anpassbaren Parameter.
    
    Standard-Konfiguration funktioniert für die meisten Fälle.
    Nur anpassen wenn Performance-Probleme auftreten.
    """)
