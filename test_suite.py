#!/usr/bin/env python3
"""
Test-Script für Financial Cockpit Komponenten.
Testet PDF-Extraktion, LLM-Integration und Berechnungen.
"""

import sys
import logging
from pathlib import Path

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Teste Ollama-Verbindung."""
    print("\n📡 Testing Ollama Connection...")
    
    from llm_extractor import check_ollama_connection, OLLAMA_BASE_URL, OLLAMA_MODEL
    
    print(f"   Ollama URL: {OLLAMA_BASE_URL}")
    print(f"   Modell: {OLLAMA_MODEL}")
    
    if check_ollama_connection():
        print("   ✅ Ollama erreichbar!")
        return True
    else:
        print("   ❌ Ollama NICHT erreichbar!")
        print("   Starte Ollama mit: ollama serve")
        return False


def test_pdf_parser():
    """Teste PDF-Parser."""
    print("\n📄 Testing PDF Parser...")
    
    # Suche nach Test-PDF
    test_pdfs = list(Path(".").glob("*.pdf")) + list(Path("uploads").glob("*.pdf"))
    
    if not test_pdfs:
        print("   ⚠️ Keine PDF-Dateien gefunden zum Testen")
        print("   Bitte lade eine PDF hoch und starte die Streamlit App")
        return False
    
    pdf_file = test_pdfs[0]
    print(f"   Teste mit: {pdf_file}")
    
    try:
        from pdf_parser import PDFParser
        
        parser = PDFParser(str(pdf_file))
        print(f"   ✅ PDF geladen: {parser.num_pages} Seiten")
        
        # Extrahiere Text
        text = parser.extract_text_all()
        print(f"   ✅ Text extrahiert: {len(text)} Zeichen")
        
        # Metadaten
        meta = parser.extract_structured_data()
        print(f"   ✅ Metadaten: {meta['filename']}")
        
        parser.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_extraction():
    """Teste LLM-Extraktion mit Test-Text."""
    print("\n🧠 Testing LLM Extraction...")
    
    from llm_extractor import extract_financials
    
    # Test mit Dummy-Text
    test_text = """
    Geschäftsjahr 2023
    Jahresüberschuss: 1.500.000 EUR
    Betriebsergebnis: 2.000.000 EUR
    Steuern: 400.000 EUR
    Zinsaufwand: 100.000 EUR
    Abschreibungen: 500.000 EUR
    Mitarbeiterzahl (Durchschnitt): 150
    """
    
    print(f"   Test-Text ({len(test_text)} Zeichen)")
    
    try:
        results = extract_financials(test_text, "TestCompany")
        
        print("   ✅ Extraktion abgeschlossen")
        
        # Zeige Ergebnisse
        for key, value in results.items():
            found = "✓" if value.get("found") else "✗"
            val = value.get("value", "N/A")
            print(f"      {found} {key}: {val}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calculations():
    """Teste EBIT/EBITDA Berechnungen."""
    print("\n🧮 Testing Financial Calculations...")
    
    from financial_calc import FinancialCalculator
    
    # Test-Daten
    test_data = {
        "operating_profit": {"value": None, "found": False, "context": ""},
        "net_profit": {"value": 1000000, "found": True, "context": "Jahresüberschuss"},
        "taxes": {"value": 300000, "found": True, "context": "Steuern"},
        "interest": {"value": 150000, "found": True, "context": "Zinsaufwand"},
        "depreciation": {"value": 500000, "found": True, "context": "Abschreibungen"},
        "employees": {"value": 250, "found": True, "unit": "number", "context": ""},
    }
    
    print("   Test-Daten:")
    print(f"      Jahresüberschuss: 1.000.000")
    print(f"      Steuern: 300.000")
    print(f"      Zinsen: 150.000")
    print(f"      Abschreibungen: 500.000")
    
    try:
        calc = FinancialCalculator(test_data)
        results = calc.get_all_calculations()
        
        print("   ✅ Berechnungen abgeschlossen")
        
        ebit = results.get("ebit", {}).get("value")
        ebitda = results.get("ebitda", {}).get("value")
        
        print(f"      EBIT: {ebit:,.0f} (Methode: {results.get('ebit', {}).get('method')})")
        print(f"      EBITDA: {ebitda:,.0f} (Methode: {results.get('ebitda', {}).get('method')})")
        
        # Verify Calculations
        expected_ebit = 1000000 + 300000 + 150000  # 1.450.000
        expected_ebitda = expected_ebit + 500000   # 1.950.000
        
        if ebit == expected_ebit and ebitda == expected_ebitda:
            print("   ✅ Berechnungen korrekt!")
            return True
        else:
            print(f"   ⚠️ Berechnungen weichen ab!")
            print(f"      Erwartet EBIT: {expected_ebit:,.0f}, Erhalten: {ebit:,.0f}")
            print(f"      Erwartet EBITDA: {expected_ebitda:,.0f}, Erhalten: {ebitda:,.0f}")
            return False
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Teste ob alle Module importierbar sind."""
    print("\n📦 Testing Python Imports...")
    
    modules = [
        ("pdf_parser", "PDFParser"),
        ("llm_extractor", "extract_financials"),
        ("financial_calc", "FinancialCalculator"),
        ("app", "None"),  # Streamlit
    ]
    
    all_ok = True
    
    for module_name, class_name in modules:
        try:
            if class_name == "None":
                __import__(module_name)
                print(f"   ✅ {module_name}")
            else:
                module = __import__(module_name)
                getattr(module, class_name)
                print(f"   ✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"   ❌ {module_name}: {e}")
            all_ok = False
        except AttributeError:
            print(f"   ⚠️ {module_name}.{class_name} nicht gefunden")
            all_ok = False
    
    return all_ok


def main():
    """Haupteinstieg."""
    print("=" * 60)
    print("🧪 Financial Cockpit - Test Suite")
    print("=" * 60)
    
    results = {}
    
    # Test Imports
    results["imports"] = test_imports()
    
    # Test Ollama
    results["ollama"] = test_ollama_connection()
    
    # Test PDF Parser (nur wenn PDFs vorhanden)
    results["pdf_parser"] = test_pdf_parser()
    
    # Test Calculations
    results["calculations"] = test_calculations()
    
    # Test LLM (nur wenn Ollama verbunden)
    if results["ollama"]:
        results["llm"] = test_llm_extraction()
    else:
        print("\n⏭️  LLM-Test übersprungen (Ollama nicht verfügbar)")
        results["llm"] = None
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    print("📊 Test Zusammenfassung:")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ BESTANDEN"
        elif result is False:
            status = "❌ FEHLGESCHLAGEN"
        else:
            status = "⏭️  ÜBERSPRUNGEN"
        
        print(f"{test_name:.<30} {status}")
    
    # Finale Empfehlung
    print("\n" + "=" * 60)
    
    if results["ollama"]:
        print("✅ AllesOK! Du kannst den Financial Cockpit starten:")
        print("\n   streamlit run app.py")
    else:
        print("⚠️  Ollama ist nicht erreichbar.")
        print("   Starte Ollama mit: ollama serve")
        print("   Dann führe die Tests erneut aus.")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
