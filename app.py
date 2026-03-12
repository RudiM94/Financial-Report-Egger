"""
Financial Cockpit - Streamlit App
Lokale Verarbeitung von Jahresabschlüssen mit semantischer LLM-Extraktion.
"""

import streamlit as st
import os
import json
import logging
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import time
import threading

# Lokale Module
from pdf_parser import PDFParser, extract_text_from_pdf
from llm_extractor import extract_financials, check_ollama_connection
from financial_calc import FinancialCalculator, format_currency

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit Konfiguration
st.set_page_config(
    page_title="Financial Cockpit",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS-Styling
st.markdown("""
<style>
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .success-text {
        color: #28a745;
        font-weight: bold;
    }
    .warning-text {
        color: #ff9800;
        font-weight: bold;
    }
    .error-text {
        color: #d32f2f;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Konstanten
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PROGRESS_FILE = DATA_DIR / ".current_analysis.json"

# Streamlit Session State initialisieren
if "ollama_connected" not in st.session_state:
    st.session_state.ollama_connected = False

if "extraction_complete" not in st.session_state:
    st.session_state.extraction_complete = False

if "company_data" not in st.session_state:
    st.session_state.company_data = {}


def load_progress():
    """Lade laufende Analyse von Datei (Persistierung über Refreshes)."""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.company_data = data.get("company_data", {})
                st.session_state.extraction_complete = data.get("complete", False)
                return True
        except:
            pass
    return False


def save_progress():
    """Speichere aktuelle Analyse in Datei (für Refresh-Persistierung)."""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                "company_data": st.session_state.company_data,
                "complete": st.session_state.extraction_complete,
                "timestamp": datetime.now().isoformat()
            }, f)
    except Exception as e:
        logger.warning(f"Konnte Progress nicht speichern: {e}")


def clear_progress():
    """Lösche gespeicherten Progress."""
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    st.session_state.extraction_complete = False
    st.session_state.company_data = {}


def _extract_in_background(text: str, company_name: str, pdf_filename: str, placeholder):
    """
    Führe Extraktion und Berechnungen im Hintergrund durch (in eigenem Thread).
    """
    try:
        # Extrahiere mit LLM
        extracted = extract_financials(text, company_name)
        
        # Berechne Kennzahlen
        calculator = FinancialCalculator(extracted)
        results = calculator.get_all_calculations()
        
        # Speichere Daten
        save_company_data(pdf_filename, company_name, results)
        
        # Aktualisiere Session State
        st.session_state.company_data = {
            "company_name": company_name,
            "filename": pdf_filename,
            "results": results
        }
        st.session_state.extraction_complete = True
        save_progress()
        
        logger.info(f"✓ Hintergrund-Extraktion für {company_name} abgeschlossen")
        
    except Exception as e:
        logger.error(f"❌ Fehler in Hintergrund-Extraktion: {e}")
        st.session_state.extraction_complete = False


def check_system_status():
    """Prüfe ob alle Abhängigkeiten verfügbar sind."""
    status = {
        "ollama": check_ollama_connection(),
        "pymupdf": True,  # Wenn das Script lädt, ist es verfügbar
        "plotly": True,
    }
    return status


def save_company_data(filename: str, company_name: str, data: dict):
    """Speichere extrahierte Company-Daten als JSON."""
    timestamp = datetime.now().isoformat()
    
    full_data = {
        "filename": filename,
        "company_name": company_name,
        "extracted_at": timestamp,
        "data": data,
    }
    
    save_path = DATA_DIR / f"{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)
    
    return save_path


def process_pdf_and_extract(pdf_file, company_name: str):
    """
    Verarbeite PDF und starte Hintergrund-Extraktion.
    Diese Funktion blockiert NICHT - startet nur die Extraktion.
    
    Returns:
        Bool indicating whether extraction was started successfully
    """
    
    with st.spinner("📄 PDF wird verarbeitet..."):
        # Speichere Upload
        uploaded_path = UPLOAD_DIR / pdf_file.name
        with open(uploaded_path, 'wb') as f:
            f.write(pdf_file.getvalue())
        
        # Extrahiere Text
        try:
            parser = PDFParser(str(uploaded_path))
            text = parser.extract_text_all()
            parser.close()
            logger.info(f"✓ Text extrahiert: {len(text)} Zeichen")
        except Exception as e:
            st.error(f"❌ Fehler beim Lesen der PDF: {e}")
            logger.error(f"PDF Parse Error: {e}")
            return False
    
    # Überprüfe Ollama
    if not check_ollama_connection():
        st.error("❌ Ollama nicht erreichbar. Bitte starten Sie Ollama.")
        return False
    
    # Starte Extraktion im Hintergrund-Thread (blockiert Streamlit NICHT)
    placeholder = st.empty()
    extraction_thread = threading.Thread(
        target=_extract_in_background,
        args=(text, company_name, pdf_file.name, placeholder),
        daemon=True
    )
    extraction_thread.start()
    
    st.info(f"🚀 Extraktion für '{company_name}' im Hintergrund gestartet")
    st.info("ℹ️ Die Seite wird alle 3 Sekunden aktualisiert - keine Weitergabe nötig!")
    
    return True


def render_metrics_section(results: dict):
    """Rendern die Metrics-Sektion mit Schlüsselzahlen."""
    
    st.subheader("📊 Key Metrics")
    
    # Erstelle 3 Spalten für Metriken
    col1, col2, col3 = st.columns(3)
    
    with col1:
        net_profit = results.get("net_profit", {}).get("value")
        if net_profit is not None:
            st.metric(
                label="Bilanzsumme",
                value=format_currency(net_profit, "EUR"),
                delta="✓ Extrahiert" if results.get("net_profit", {}).get("found") else "⚠️ Berechnet"
            )
        else:
            st.metric(label="Bilanzsumme", value="N/A")
    
    with col2:
        ebit = results.get("ebit", {}).get("value")
        if ebit is not None:
            method_text = "Extrahiert" if results.get("ebit", {}).get("method") == "direct" else "Berechnet"
            st.metric(
                label="EBIT",
                value=format_currency(ebit, "EUR"),
                delta=f"✓ {method_text}"
            )
        else:
            st.metric(label="EBIT", value="N/A")
    
    with col3:
        ebitda = results.get("ebitda", {}).get("value")
        if ebitda is not None:
            st.metric(
                label="EBITDA",
                value=format_currency(ebitda, "EUR"),
                delta="✓ Berechnet"
            )
        else:
            st.metric(label="EBITDA", value="N/A")
    
    # Zweite Reihe: Weitere Kennzahlen
    col4, col5, col6 = st.columns(3)
    
    with col4:
        taxes = results.get("taxes", {}).get("value")
        if taxes is not None:
            st.metric(
                label="Steuern",
                value=format_currency(taxes, "EUR"),
                delta="✓ Extrahiert" if results.get("taxes", {}).get("found") else "⚠️ Berechnet"
            )
        else:
            st.metric(label="Steuern", value="N/A")
    
    with col5:
        depreciation = results.get("depreciation", {}).get("value")
        if depreciation is not None:
            st.metric(
                label="Abschreibungen",
                value=format_currency(depreciation, "EUR"),
                delta="✓ Extrahiert" if results.get("depreciation", {}).get("found") else "⚠️ Berechnet"
            )
        else:
            st.metric(label="Abschreibungen", value="N/A")
    
    with col6:
        employees = results.get("employees", {}).get("value")
        if employees is not None:
            st.metric(
                label="Mitarbeiter",
                value=f"{int(employees):,}",
                delta="✓ Extrahiert" if results.get("employees", {}).get("found") else "⚠️ Berechnet"
            )
        else:
            st.metric(label="Mitarbeiter", value="N/A")


def render_comparison_chart(results: dict):
    """Rendere Vergleichs-Balkendiagramm EBIT vs EBITDA."""
    
    st.subheader("📈 EBIT vs EBITDA Vergleich")
    
    ebit = results.get("ebit", {}).get("value")
    ebitda = results.get("ebitda", {}).get("value")
    
    if ebit is not None or ebitda is not None:
        data = {}
        if ebit is not None:
            data["EBIT"] = ebit
        if ebitda is not None:
            data["EBITDA"] = ebitda
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(data.keys()),
                y=list(data.values()),
                marker_color=['#1f77b4', '#ff7f0e'],
                text=[format_currency(v, "EUR") for v in data.values()],
                textposition='auto',
            )
        ])
        
        fig.update_layout(
            title="EBIT vs EBITDA",
            xaxis_title="Metrik",
            yaxis_title="Wert (EUR)",
            hovermode='x unified',
            showlegend=False,
            height=400,
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Keine Daten für Vergleich verfügbar")


def render_data_sources(results: dict):
    """Zeige Informationen über Datenquellen (direkt vs berechnet)."""
    
    st.subheader("ℹ️ Datenquellen & Berechnungsmethoden")
    
    with st.expander("Details zur Datenextraktion", expanded=False):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Direkt extrahierte Werte:**")
            
            direct_values = []
            
            metrics = ["operating_profit", "net_profit", "taxes", "interest", "depreciation", "employees"]
            
            for metric in metrics:
                if results.get(metric, {}).get("found"):
                    value = results.get(metric, {}).get("value")
                    context = results.get(metric, {}).get("context", "")[:100]
                    direct_values.append(f"✓ {metric}: {value} ({context}...)")
            
            if direct_values:
                for val in direct_values:
                    st.text(val)
            else:
                st.text("Keine direkt extrahierten Werte gefunden")
        
        with col2:
            st.write("**Berechnete Werte:**")
            
            ebit_method = results.get("ebit", {}).get("method", "not_calculated")
            ebit_note = results.get("ebit", {}).get("note", "")
            
            st.write(f"**EBIT:** {ebit_method}")
            if ebit_note:
                st.caption(ebit_note)
            
            ebitda_method = results.get("ebitda", {}).get("method", "not_calculated")
            ebitda_note = results.get("ebitda", {}).get("note", "")
            
            st.write(f"**EBITDA:** {ebitda_method}")
            if ebitda_note:
                st.caption(ebitda_note)


def render_full_data_table(results: dict):
    """Zeige Tabelle mit allen Daten."""
    
    st.subheader("📋 Vollständige Datenübersicht")
    
    with st.expander("Alle Werte anzeigen", expanded=False):
        
        # Konvertiere in Tabellen-Format
        table_data = []
        
        for key, value in results.items():
            if isinstance(value, dict) and "value" in value:
                found = "✓" if value.get("found") else "✗"
                val = value.get("value", "N/A")
                method = value.get("method", value.get("currency", "EUR"))
                
                table_data.append({
                    "Metrik": key,
                    "Wert": format_currency(val, "EUR") if isinstance(val, (int, float)) else str(val),
                    "Gefunden": found,
                    "Quelle": method,
                })
        
        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )


def render_sidebar():
    """Rendere Sidebar mit Status und Einstellungen."""
    
    with st.sidebar:
        st.title("⚙️ Financial Cockpit")
        st.divider()
        
        # Zeige Extraction-Fortschritt
        progress_file = DATA_DIR / ".extraction_progress.json"
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    progress = json.load(f)
                    company = progress.get("company_name", "Analyse")
                    chunks = progress.get("chunks_completed", 0)
                    total = progress.get("total_chunks", 0)
                    percentage = progress.get("percentage", 0)
                    
                    st.info(f"⏳ **{company}**\n\nChunks: {chunks}/{total} ({percentage}%)", icon="⏳")
                    st.progress(percentage / 100.0)
                    st.divider()
            except:
                pass
        
        # Zeige laufende Analyse wenn keine aktuellen Chunks
        if st.session_state.company_data and not st.session_state.extraction_complete:
            st.info(f"📊 Fertig gestellt: **{st.session_state.company_data.get('company_name', 'PDF')}**", icon="✅")
            st.divider()
        elif PROGRESS_FILE.exists() and not st.session_state.extraction_complete:
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
                    st.info(f"💾 Laufende Analyse: **{progress.get('company_data', {}).get('company_name', 'PDF')}**", icon="💾")
                    st.divider()
            except:
                pass
        
        # System Status
        st.subheader("System Status")
        status = check_system_status()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Ollama:**")
            if status["ollama"]:
                st.success("✓ Verbunden")
            else:
                st.error("✗ Nicht erreichbar")
        
        with col2:
            st.write("**PyMuPDF:**")
            st.success("✓ Verfügbar")
        
        st.divider()
        
        # Dokumentation
        st.subheader("📖 Dokumentation")
        
        st.write("""
        ### Wie der Financial Cockpit funktioniert:
        
        1. **PDF-Upload:** Lade einen Jahresabschluss hoch
        2. **Text-Extraktion:** PyMuPDF liest den PDF-Text
        3. **Semantische Analyse:** Lokales LLM (Ollama) findet Finanzdaten
        4. **Berechnungen:** Python berechnet EBIT und EBITDA aus Rohdaten
        5. **Visualisierung:** Dashboard zeigt Key Metrics und Diagramme
        
        ### Unterstützte deutsche Fachbegriffe:
        
        - **Betriebsergebnis** = Operating Profit / EBIT
        - **Bilanzsumme** = Net Profit / Jahresüberschuss
        - **Steuern** = Income Taxes
        - **Zinsaufwand** = Interest Expense
        - **Abschreibungen** = Depreciation
        - **Mitarbeiter** = Employees
        """)
        
        st.divider()
        
        # Info
        st.info("""
        💡 **Info:** Der Financial Cockpit nutzt ein lokales LLM 
        (Ollama mit llama3 oder mistral) für 100% lokale Datenverarbeitung.
        Alle Daten bleiben auf deinem Computer!
        """)


def main():
    """Hauptfunktion der Streamlit App."""
    
    st.title("📊 Financial Cockpit")
    st.markdown("*Lokale Verarbeitung von Jahresabschlüssen mit semantischer LLM-Extraktion*")
    
    # Lade gespeicherte Analyse bei Seitenrefresh
    load_progress()
    
    st.divider()
    
    # Rendere Sidebar
    render_sidebar()
    
    # Auto-Refresh wenn Extraction läuft
    progress_file = DATA_DIR / ".extraction_progress.json"
    if progress_file.exists():
        st.markdown("#### ⏳ Analyse läuft... Sie können die Seite aktualisieren um den Fortschritt zu sehen.")
        time.sleep(3)  # Warte 3 Sekunden vor Auto-Refresh
        st.rerun()
    
    # Prüfe Ollama-Verbindung
    if not st.session_state.ollama_connected:
        if check_ollama_connection():
            st.session_state.ollama_connected = True
        else:
            st.error("""
            ❌ **Ollama nicht erreichbar!**
            
            Stelle sicher, dass Ollama lokal läuft:
            ```bash
            ollama serve
            ```
            
            Oder starte auf einem bestimmten Port:
            ```bash
            OLLAMA_HOST=localhost:11434 ollama serve
            ```
            """)
            return
    
    # Haupt-Interface
    st.subheader("📁 Jahresabschluss hochladen")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Wähle eine PDF-Datei (Jahresabschluss):",
            type=["pdf"],
            help="Unterstützt Jahresabschlüsse, Geschäftsberichte, Finanzberichte in PDF-Format"
        )
    
    with col2:
        company_name = st.text_input(
            "Unternehmensname:",
            value="Unbekanntes Unternehmen",
            help="Name des Unternehmens für Datenorganisation"
        )
    
    st.divider()
    
    # Verarbeite Upload
    if uploaded_file is not None:
        st.success(f"✓ Datei ausgewählt: {uploaded_file.name}")
        
        if st.button("🚀 Analyse starten", use_container_width=True, type="primary"):
            success = process_pdf_and_extract(uploaded_file, company_name)
            # Die Extraktion läuft jetzt im Hintergrund - Streamlit aktualisiert sich selbst
    
    # Zeige Ergebnisse wenn verfügbar
    if st.session_state.extraction_complete and st.session_state.company_data:
        
        st.divider()
        
        data = st.session_state.company_data
        results = data["results"]
        
        st.markdown(f"### Analyse für: **{data['company_name']}**")
        st.caption(f"Datei: {data['filename']}")
        
        # Rendern Sie verschiedene Sections
        render_metrics_section(results)
        
        st.divider()
        
        render_comparison_chart(results)
        
        st.divider()
        
        render_data_sources(results)
        
        st.divider()
        
        render_full_data_table(results)
        
        # Download Button
        col1, col2 = st.columns(2)
        
        with col1:
            json_str = json.dumps(results, indent=2, default=str, ensure_ascii=False)
            st.download_button(
                label="📥 Daten als JSON herunterladen",
                data=json_str,
                file_name=f"{data['company_name']}_analysis.json",
                mime="application/json"
            )
        
        with col2:
            if st.button("🔄 Neue Analyse", use_container_width=True):
                clear_progress()
                st.rerun()


if __name__ == "__main__":
    main()
