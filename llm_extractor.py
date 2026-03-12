"""
LLM-basierte semantische Extraktion von Finanzdaten aus Jahresabschlüssen.
Nutzt lokales Ollama-Server für 100% lokale Verarbeitung.
"""

import requests
import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional, List
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Ollama Server Konfiguration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"  # oder "mistral", je nachdem was installiert ist

# Deutsche Fachbegriffe für Finanzmetriken
GERMAN_TERMS = {
    "operating_profit": [
        "Betriebsergebnis", "Operatives Ergebnis", "Operating results",
        "EBIT", "Gewinn aus betrieblicher Tätigkeit", "Ergebnis der Betriebstätigkeit"
    ],
    "net_profit": [
        "Jahresüberschuss", "Gewinn", "Net income", "Gewinne",
        "Jahresergebnis", "Periodenergebnis", "Konzerngewinn"
    ],
    "taxes": [
        "Steuern vom Einkommen", "Ertragsteuern", "Income tax",
        "Einkommensteuer", "Körperschaftsteuer", "Gewerbesteuer",
        "Steuern auf der Gewinn", "Ertragsteuerabgaben"
    ],
    "interest": [
        "Zinsaufwand", "Zinsergebnis", "Interest expense",
        "Finanzierungskosten", "Zinskosten", "Zinsertragsaufwand",
        "Aufwendungen für Zinsen"
    ],
    "depreciation": [
        "Abschreibungen", "Depreciation", "Amortization",
        "Abschreibungen auf immaterielles Vermögen",
        "Abschreibungen Sachanlagen", "Wertminderungen"
    ],
    "employees": [
        "Mitarbeiter", "Employees", "Arbeitnehmer",
        "Durchschnittliche Anzahl", "Mitarbeiterzahl", "Personalstand",
        "Beschäftigte"
    ]
}


def check_ollama_connection() -> bool:
    """Prüfe ob Ollama-Server erreichbar ist."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama nicht erreichbar: {e}")
        return False


def chunk_text(text: str, chunk_size: int = 3000, overlap: int = 300) -> List[str]:
    """
    Teile Text in Chunks auf mit Überlappung, um Kontext zu erhalten.
    
    Args:
        text: Zu chunkendes Text
        chunk_size: Größe eines Chunks in Zeichen
        overlap: Überlappungsgröße zwischen Chunks
    
    Returns:
        Liste von Text-Chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def build_extraction_prompt(text_chunk: str, metrics: List[str]) -> str:
    """
    Baue den Extraktions-Prompt für das LLM.
    
    Args:
        text_chunk: Text-Chunk aus PDF
        metrics: Liste der zu extrahierenden Metriken
    
    Returns:
        Der Prompt als String
    """
    metrics_description = "\n".join([
        "- Betriebsergebnis / Operating Profit (EBIT): Gewinn vor Zinsen und Steuern",
        "- Jahresüberschuss / Net Profit: Gewinn nach Steuern",
        "- Steuern vom Einkommen / Taxes: Ertragsteuern",
        "- Zinsaufwand / Interest Expense: Zinskosten",
        "- Abschreibungen / Depreciation: Wertminderungen auf Vermögenswerte",
        "- Mitarbeiteranzahl / Employees: Durchschnittliche Zahl im Jahr"
    ])
    
    prompt = f"""Du bist ein Experte für die Analyse von Jahresabschlüssen und Finanzberichten.

Analysiere den folgenden Text aus einem Jahresabschluss und extrahiere gezielt folgende Finanzkennzahlen:

GESUCHTE METRIKEN:
{metrics_description}

TEXT ZUM ANALYSIEREN:
{text_chunk}

WICHTIGE FORMATIERUNGSANWEISUNG:
Alle Zahlen MÜSSEN im englischen Format sein, KEINE deutschen Formate!
- RICHTIG: 1234567, 123456.79, -456789
- FALSCH: 1.234.567, 1,23, 1.234.567,89

JSON-STRUKTUR:
{{
  "operating_profit": {{
    "value": <Zahl (z.B. 1234567) ODER null>,
    "currency": "EUR" oder "USD",
    "found": true oder false,
    "context": "Kurze Beschreibung wo der Wert gefunden wurde"
  }},
  "net_profit": {{
    "value": <Zahl ODER null>,
    "currency": "EUR" oder "USD",
    "found": true oder false,
    "context": ""
  }},
  "taxes": {{
    "value": <Zahl ODER null>,
    "currency": "EUR" oder "USD",
    "found": true oder false,
    "context": ""
  }},
  "interest": {{
    "value": <Zahl ODER null>,
    "currency": "EUR" oder "USD",
    "found": true oder false,
    "context": ""
  }},
  "depreciation": {{
    "value": <Zahl ODER null>,
    "currency": "EUR" oder "USD",
    "found": true oder false,
    "context": ""
  }},
  "employees": {{
    "value": <ganze Zahl ODER null>,
    "unit": "number",
    "found": true oder false,
    "context": ""
  }}
}}

ANWEISUNG:
1. Suche nach den Werten deutsch und englisch
2. Zahlen IMMER ohne Punkte (1234567 nicht 1.234.567)
3. Falls dezimal: 1234567.89 nicht 1234567,89
4. Antworte NUR mit gültigem JSON Code-Block:
```json
{{ ... dein JSON hier ... }}
```
Kein anderer Text, kein deutsch vorher/nachher!
"""
    
    return prompt


def call_ollama_api(prompt: str, max_retries: int = 3) -> Optional[str]:
    """
    Rufe die Ollama API auf mit Retry-Logik.
    
    Args:
        prompt: Der Prompt
        max_retries: Maximale Anzahl von Wiederholungen
    
    Returns:
        Die Antwort vom LLM oder None bei Fehler
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Niedrige Temperatur für konsistente Extraktion
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                logger.warning(f"Ollama API Fehler (Attempt {attempt + 1}): {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout bei Ollama API (Attempt {attempt + 1})")
        except Exception as e:
            logger.error(f"Fehler bei Ollama API-Aufruf (Attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None


def parse_json_response(response_text: str) -> Optional[Dict]:
    """
    Parse die JSON-Antwort vom LLM, auch wenn sie mit Text umgeben ist.
    Handles JSON in code blocks (```json ... ```), plain JSON, or raw objects.
    Normalizes German number formats (1.234.567,89 -> 1234567.89).
    
    Args:
        response_text: Die Rohtext-Antwort vom LLM
    
    Returns:
        Das geparste JSON-Dict oder None
    """
    if not response_text:
        return None
    
    # Versuche direktes JSON-Parsing
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Versuche JSON in ```json ... ``` Code-Block zu extrahieren
    try:
        # Suche nach ```json oder ```
        code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_block_match:
            json_str = code_block_match.group(1).strip()
            # Normalisiere deutsche Zahlenformate vor JSON-Parsing
            json_str = _normalize_numbers(json_str)
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Versuche JSON zwischen {} zu extrahieren
    try:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            # Normalisiere deutsche Zahlenformate vor JSON-Parsing
            json_str = _normalize_numbers(json_str)
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    logger.warning("Konnte JSON aus LLM-Antwort nicht parsen. Response: %s", response_text[:200])
    return None


def _normalize_numbers(json_str: str) -> str:
    """
    Normalisiere deutsche Zahlenformate in JSON-String.
    Konvertiert: 1.234.567,89 -> 1234567.89 und 1.234.567 -> 1234567
    
    Args:
        json_str: Der JSON-String mit möglicherweise deutschen Zahlenformaten
    
    Returns:
        Normalisierter JSON-String mit englischen Zahlenformaten
    """
    def convert_german_to_english_number(match):
        """Konvertiert deutsche Zahlenformate zu englischen."""
        num_str = match.group(0)
        
        # Fall 1: Zahlen mit Komma UND Punkte (z.B. 1.234.567,89)
        # Entferne alle Punkte, ersetze Komma mit Punkt
        if ',' in num_str and '.' in num_str:
            return num_str.replace('.', '').replace(',', '.')
        
        # Fall 2: Zahlen NUR mit Komma (z.B. 123,45)
        # Komma ist Dezimaltrennzeichen
        if ',' in num_str and '.' not in num_str:
            return num_str.replace(',', '.')
        
        # Fall 3: Zahlen NUR mit Punkten (z.B. 1.234.567)
        # Punkte sind Tausendertrennzeichen -> entferne alle
        if '.' in num_str and ',' not in num_str:
            # Prüfe ob es Tausenderformat ist (mehrere Punkte oder 3+ Ziffern dann Punkt)
            if num_str.count('.') >= 1:  # Mindestens ein Punkt
                return num_str.replace('.', '')
        
        return num_str
    
    # Pattern zum Erkennen von Zahlen (deutsch oder englisch)
    # Matches: -? für optional Minus
    # (\d{1,3}[.,])* für optionale Tausender-Gruppen
    # \d+ für Ziffernteile
    # ([.,]\d+)? für optionales Dezimal-Teil
    pattern = r'-?(?:\d{1,3}[.,])+\d+(?:[.,]\d+)?|-?\d+[.,]\d+|-?\d{1,3}(?:\.\d{3})+(?:,\d+)?'
    
    result = re.sub(pattern, convert_german_to_english_number, json_str)
    return result


def extract_financials(text: str, company_name: str = "Unknown") -> Dict[str, Dict]:
    """
    Extrahiere Finanzmetriken aus Text mittels lokalem LLM.
    
    Diese Funktion teilt lange Texte in Chunks auf, sendet sie an Ollama,
    und kombiniert die Ergebnisse intelligent.
    
    Args:
        text: Der vollständige Text aus dem PDF
        company_name: Name des Unternehmens (für Logging)
    
    Returns:
        Dict mit extrahierten Finanzdaten
    """
    
    logger.info(f"Starte Finanzextraktion für {company_name}")
    
    # Prüfe Ollama-Verbindung
    if not check_ollama_connection():
        logger.error("Ollama nicht erreichbar!")
        return _create_empty_result()
    
    # Teile Text in Chunks
    chunks = chunk_text(text, chunk_size=3000, overlap=300)
    logger.info(f"Text in {len(chunks)} Chunks aufgeteilt")
    
    # Speichere alle Ergebnisse pro Chunk
    all_results = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Verarbeite Chunk {i + 1}/{len(chunks)}")
        
        # Speichere Progress
        _save_progress(company_name, i + 1, len(chunks))
        
        prompt = build_extraction_prompt(chunk, list(GERMAN_TERMS.keys()))
        response = call_ollama_api(prompt)
        
        if response:
            parsed = parse_json_response(response)
            if parsed:
                all_results.append(parsed)
        
        time.sleep(0.5)  # Rate limiting
    
    # Kombiniere Ergebnisse intelligently - nutze erste gefundenen Wert
    combined_result = _combine_results(all_results)
    
    logger.info(f"Extraktion abgeschlossen. Die Anzahl der Chunks: {len(all_results)}")
    
    # Lösche Progress-Datei nach Abschluss
    _clear_progress()
    
    return combined_result


def _combine_results(all_results: List[Dict]) -> Dict[str, Dict]:
    """
    Kombiniere Ergebnisse aus mehreren Chunks intelligent.
    Nutze den ersten gefundenen Wert für jede Metrik.
    """
    combined = _create_empty_result()
    
    # Für jede Metrik, nutze den ersten gefundenen Wert
    metrics = ["operating_profit", "net_profit", "taxes", "interest", "depreciation", "employees"]
    
    for metric in metrics:
        for result in all_results:
            if metric in result and result[metric].get("found"):
                combined[metric] = result[metric]
                break
    
    return combined


def _create_empty_result() -> Dict[str, Dict]:
    """Erstelle eine leere Result-Struktur."""
    return {
        "operating_profit": {"value": None, "currency": "EUR", "found": False, "context": ""},
        "net_profit": {"value": None, "currency": "EUR", "found": False, "context": ""},
        "taxes": {"value": None, "currency": "EUR", "found": False, "context": ""},
        "interest": {"value": None, "currency": "EUR", "found": False, "context": ""},
        "depreciation": {"value": None, "currency": "EUR", "found": False, "context": ""},
        "employees": {"value": None, "unit": "number", "found": False, "context": ""},
    }


def _save_progress(company_name: str, chunks_done: int, total_chunks: int):
    """Speichere Verarbeitungsfortschritt in Datei."""
    try:
        progress_file = Path("data") / ".extraction_progress.json"
        progress_data = {
            "company_name": company_name,
            "chunks_completed": chunks_done,
            "total_chunks": total_chunks,
            "percentage": int((chunks_done / total_chunks) * 100) if total_chunks > 0 else 0,
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f)
        logger.debug(f"Progress: {chunks_done}/{total_chunks} ({progress_data['percentage']}%)")
    except Exception as e:
        logger.warning(f"Konnte Progress nicht speichern: {e}")


def _clear_progress():
    """Lösche Progress-Datei nach Abschluss."""
    try:
        progress_file = Path("data") / ".extraction_progress.json"
        if progress_file.exists():
            progress_file.unlink()
    except Exception as e:
        logger.warning(f"Konnte Progress-Datei nicht löschen: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Teste Verbindung
    if check_ollama_connection():
        print("✓ Ollama ist erreichbar")
    else:
        print("✗ Ollama nicht erreichbar. Starte mit: ollama serve")
