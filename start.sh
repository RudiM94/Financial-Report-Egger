#!/bin/bash

# Financial Cockpit - Start Script
# Dieser Script startet alle notwendigen Komponenten

echo "📊 Financial Cockpit - Startroutine"
echo "=================================="
echo ""

# Prüfe ob Ollama läuft
echo "1️⃣  Prüfe Ollama..."
if pgrep -x "ollama" > /dev/null; then
    echo "   ✅ Ollama läuft"
else
    echo "   ⚠️  Ollama läuft NICHT!"
    echo "   Starte in separatem Terminal: ollama serve"
    echo ""
    read -p "   Drücke Enter wenn Ollama läuft..."
fi

echo ""
echo "2️⃣  Richte Python-Umgebung ein..."

# Prüfe Virtual Environment
if [ ! -d "venv" ]; then
    echo "   Erstelle Virtual Environment..."
    python3 -m venv venv
fi

# Aktiviere Virtual Environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "   ✅ Virtual Environment aktiviert"
else
    echo "   ⚠️ Aktivierung fehlgeschlagen"
    exit 1
fi

echo ""
echo "3️⃣  Installiere Dependencies..."

# Prüfe ob requirements.txt vorhanden
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo "   ✅ Dependencies installiert"
else
    echo "   ❌ requirements.txt nicht gefunden!"
    exit 1
fi

echo ""
echo "4️⃣  Führe Tests durch..."

python3 test_suite.py

echo ""
echo "5️⃣  Starte Streamlit App..."
echo ""

# Starte Streamlit
streamlit run app.py

# Cleanup
deactivate
