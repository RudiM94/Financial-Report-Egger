# 📊 Financial Cockpit

Ein lokales System zur semantischen Extraktion von Finanzdaten aus Jahresabschlüssen mit einem lokalen LLM (Ollama) und Python-Berechnungen.

## Features

✅ **100% Lokal** - Alle Daten bleiben auf deinem Computer
✅ **PDF-Verarbeitung** - Unterstützt Jahresabschlüsse, Geschäftsberichte in PDF
✅ **Semantische Extraktion** - Nutzt lokales LLM (llama3/mistral) statt Regex
✅ **Intelligente Berechnungen** - Berechnet EBIT und EBITDA sicher in Python
✅ **Deutsche Fachbegriffe** - Versteht Betriebsergebnis, Jahresüberschuss, etc.
✅ **Interaktives Dashboard** - Streamlit Frontend mit Metriken und Diagrammen
✅ **JSON-Export** - Speichert und exportiert Ergebnisse

## Architektur

```
financial_cockpit/
├── app.py                 # Streamlit Frontend
├── pdf_parser.py         # PyMuPDF PDF-Extraktion
├── llm_extractor.py      # Ollama LLM-Integration
├── financial_calc.py     # EBIT/EBITDA Berechnungen
├── requirements.txt      # Python Abhängigkeiten
├── data/                 # Gespeicherte JSON-Ergebnisse
└── uploads/              # Hochgeladene PDFs
```

## Installation

### 1. Prerequisites

- Python 3.9+
- Ollama lokaler Server (für LLM)
- macOS/Linux/Windows

### 2. Ollama installieren

```bash
# macOS:
brew install ollama

# oder von https://ollama.ai downloaden

# Starte Ollama:
ollama serve

# In separatem Terminal: Lade Modell herunter
ollama pull llama3        # oder mistral
```

### 3. Python Umgebung

```bash
cd financial_cockpit

# Virtual Environment erstellen (optional aber empfohlen)
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Verwendung

### Streamlit App starten

```bash
cd financial_cockpit

# Mit venv:
source venv/bin/activate

# Starte Streamlit:
streamlit run app.py

# Die App öffnet sich unter: http://localhost:8501
```

### Verwendungsfluss

1. **PDF hochladen** - Wähle einen Jahresabschluss
2. **Unternehmensname eingeben** - Für Datenorganisation
3. **"Analyse starten" klicken** - Der Financial Cockpit arbeitet:
   - Extrahiert Text mit PyMuPDF
   - Sendet in Chunks an lokales LLM
   - LLM sucht Finanzkennzahlen
   - Python berechnet EBIT und EBITDA
   - Speichert Ergebnisse als JSON
4. **Dashboard anschauen** - Key Metrics, Diagramme, Datenquellen
5. **JSON exportieren** - Für weitere Verarbeitung

## Extrahierte Finanzkennzahlen

| Kennzahl | Deutsche Begriffe | Beschreibung |
|----------|------------------|---------------|
| **Operating Profit** | Betriebsergebnis, EBIT | Gewinn vor Zinsen und Steuern |
| **Net Profit** | Jahresüberschuss, Gewinn | Gewinn nach Steuern |
| **Taxes** | Steuern, Ertragsteuern | Einkommensteuer, Körperschaftsteuer |
| **Interest Expense** | Zinsaufwand, Zinsergebnis | Zinskosten |
| **Depreciation** | Abschreibungen | Wertminderungen auf Vermögenswerte |
| **Employees** | Mitarbeiterzahl, Personalstand | Durchschnittliche Mitarbeiter im Jahr |
| **EBIT** | Betriebsergebnis | Berechnet: Net Profit + Taxes + Interest |
| **EBITDA** | - | Berechnet: EBIT + Depreciation |

## Berechnungslogik

### EBIT Berechnung

```
Priorität 1: Wenn "Betriebsergebnis" direkt gefunden → nutze diesen Wert

Priorität 2: Berechne aus Komponenten
    EBIT = Jahresüberschuss + Steuern + Zinsen
    
    Logik:
    - Net Profit = (EBIT - Interest) - Taxes
    - Umgestellt: EBIT = Net Profit + Taxes + Interest
```

### EBITDA Berechnung

```
EBITDA = EBIT + Abschreibungen

Wenn Abschreibungen fehlen:
    EBITDA = EBIT (mit Warnung)
```

**Warum Python rechnet, nicht das LLM:**
- LLMs sind schlecht im Rechnen
- Python garantiert Genauigkeit
- Trennwertung: LLM findet Rohdaten, Python rechnet

## Technische Details

### PDF Verarbeitung (pdf_parser.py)

```python
from pdf_parser import PDFParser

parser = PDFParser("path/to/pdf")
text = parser.extract_text_all()  # Extrahiert kompletten Text
metadata = parser.extract_structured_data()  # Metadaten
parser.close()
```

### LLM Integration (llm_extractor.py)

```python
from llm_extractor import extract_financials

# Ollama API wird automatisch kontaktiert
results = extract_financials(text, company_name="Mein Unternehmen")

# Rückgabe Format:
{
    "operating_profit": {"value": 1000000, "found": true, "context": "..."},
    "net_profit": {"value": 750000, "found": true, "context": "..."},
    ...
}
```

### Berechnungen (financial_calc.py)

```python
from financial_calc import FinancialCalculator

calculator = FinancialCalculator(extracted_data)
results = calculator.get_all_calculations()

# results enthält alle Werte + EBIT/EBITDA mit Berechnungsmethode
```

## Fehlerbehandlung & Robustheit

✅ **Ollama nicht erreichbar** → App zeigt Fehler, gibt Anleitung
✅ **PDF nicht lesbar** → Fehlerbehandlung mit Logging
✅ **LLM findet Wert nicht** → Defaultet auf None mit Warnung
✅ **Zu viele fehlende Werte** → EBIT/EBITDA können nicht berechnet werden
✅ **Lange Texte** → Text wird in Chunks mit Überlappung verarbeitet
✅ **JSON-Parsing-Fehler** → Fallbacks für LLM-Antworten

## Datenfluss Diagramm

```
┌─────────────────┐
│  PDF hochladen  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ PyMuPDF extrahiert Text │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│  Text in Chunks teilen   │
│ (mit Überlappung)        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────┐
│ Ollama LLM (lokal)               │
│ - Sucht Finanzkennzahlen         │
│ - Gibt JSON zurück               │
└────────┬─────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Python berechnet:            │
│ - EBIT (aus Components)      │
│ - EBITDA (EBIT + Deprec.)   │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Streamlit Dashboard      │
│ - Key Metrics            │
│ - Diagramme              │
│ - Datenquellen Info      │
└──────────────────────────┘
```

## Konfiguration

### Ollama Modell ändern

In `llm_extractor.py`:

```python
OLLAMA_MODEL = "mistral"  # oder "llama3", "neural-chat", etc.
```

### Ollama Server Port

Standard: `http://localhost:11434`

Bei abweichenddem Port in `llm_extractor.py` anpassen:

```python
OLLAMA_BASE_URL = "http://localhost:11435"  # dein Port
```

### Temperature ändern (Genauigkeit vs Kreativität)

In `llm_extractor.py`:

```python
"temperature": 0.3,  # Niedrig = zuverlässiger
                     # Hoch = kreativ aber weniger zuverlässig
```

## Logging

Logs werden auf `INFO` Level zu weiß ausgegeben:

```
INFO:__main__:PDF geöffnet: example.pdf (45 Seiten)
INFO:__main__:Text in 5 Chunks aufgeteilt
INFO:__main__:EBIT berechnet: 500000
```

Für Debug-Mode in den Modulen wechsel zu `DEBUG`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Tipps & Best Practices

### Für beste Ergebnisse:

1. **Hochauflösende PDFs** - Bessere Text-Extraktion
2. **Deutsche Jahresabschlüsse** - LLM ist auf Deutsch optimiert
3. **Ollama Cache** - Erste Anfrage dauert länger, danach schneller
4. **Ausreichend RAM** - Mindestens 4GB für llama3
5. **Chunk-Größe optimieren** - Bei sehr langen Dokumenten bearbeiten

### Troubleshooting

**"Ollama nicht erreichbar"**
```bash
# Prüfe ob Ollama läuft:
ps aux | grep ollama

# Starte Ollama:
ollama serve
```

**"Modell nicht gefunden"**
```bash
# Verfügbare Modelle:
ollama list

# Modell herunterladen:
ollama pull llama3
```

**"Timeout bei LLM-Anfrage"**
→ Erhöhe Timeout in `llm_extractor.py`:
```python
response = requests.post(..., timeout=120)  # von 60 erhöht
```

**"Keine Werte werden extrahiert"**
→ Prüfe die Logs, möglicherweise:
- Falsches PDF-Format (gescannt statt digital)
- Ungewöhnliches Layout
- Nicht-deutsche Begriffe

## Performance

| Schritt | Dauer |
|---------|-------|
| PDF-Text extrahieren | 1-5 Sek |
| LLM Extraktion (1 Chunk) | 5-15 Sek |
| Berechnungen | < 1 Sek |
| **Gesamt (normale PDF)** | **15-45 Sek** |

## Lizenz

Diese Software ist Open Source.

## Support

Bei Fragen oder Issues:
1. Poste im GitHub Issues
2. Check die Logs in `logging.basicConfig(level=logging.DEBUG)`
3. Stelle sicher Ollama läuft: `ps aux | grep ollama`

---

**Financial Cockpit** - Deine lokale Finanzanalyse-Suite 📊
