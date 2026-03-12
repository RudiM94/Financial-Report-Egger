# 🚀 QUICKSTART - Financial Cockpit

## 1️⃣ Stelle sicher, Ollama läuft

```bash
# Terminal 1: Starte Ollama Server
ollama serve

# Terminal 2: Lade Modell (optional, falls noch nicht vorhanden)
ollama pull llama3   # oder mistral
```

## 2️⃣ Installiere Dependencies

```bash
# Navigiere ins Verzeichnis
cd financial_cockpit

# Virtual Environment (optional aber empfohlen)
python3 -m venv venv
source venv/bin/activate

# Installiere Packages
pip install -r requirements.txt
```

## 3️⃣ Starte die App

```bash
# Mit Streamlit
streamlit run app.py

# App öffnet sich unter: http://localhost:8501
```

## 4️⃣ Teste dein System (Optional)

```bash
# Vor dem ersten Use, teste alle Komponenten:
python3 test_suite.py

# Sollte zeigen:
# ✅ imports
# ✅ ollama
# ✅ calculations
# ✅ llm
```

## 5️⃣ Nutze den Financial Cockpit

1. 📁 **Upload** - Jahresabschluss-PDF hochladen
2. 📝 **Eingabe** - Unternehmensname eingeben
3. 🚀 **Analyse** - Button "Analyse starten" klicken
4. 📊 **Dashboard** - Ergebnisse ansehen
5. 📥 **Export** - JSON exportieren

## 📋 Verwendetes Beispiel

```python
# Wenn du die Module direkt nutzen möchtest:

from pdf_parser import PDFParser
from llm_extractor import extract_financials
from financial_calc import FinancialCalculator

# 1. PDF laden
parser = PDFParser("my_financial_report.pdf")
text = parser.extract_text_all()

# 2. LLM extrahieren
results = extract_financials(text, "Mein Unternehmen")

# 3. Berechnen
calculator = FinancialCalculator(results)
final_data = calculator.get_all_calculations()

print(f"EBIT: {final_data['ebit']['value']}")
print(f"EBITDA: {final_data['ebitda']['value']}")
```

## 🆘 Troubleshooting

**"Ollama nicht erreichbar"**
```bash
# Starten Sie Ollama:
ollama serve

# Prüfe ob Process läuft:
ps aux | grep ollama
```

**"API Fehler 404"**
→ Sicherstellen, dass das Modell heruntergeladen ist:
```bash
ollama pull llama3
```

**"ImportError: No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

**"Timeout bei LLM"**
→ Normales Verhalten bei langen PDFs. Warte patiivly.

## 📚 Dokumentation

Vollständige Dokumentation: Siehe [README.md](README.md)

## Performance-Tipps

- **Erste Anfrage**: LLM-Modelle benötigen ~10-30s beim ersten Load
- **Danach**: ~5-15s pro 3000-Zeichen-Chunk
- **RAM**: Mindestens 4GB für llama3
- **CPU**: Multi-Core besser

---

**Du bist bereit! 🎉 Starte deine Finanzanalyse jetzt!**

```bash
streamlit run app.py
```
