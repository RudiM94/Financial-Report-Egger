"""
Erweiterte Beispiele für Financial Cockpit.
Zeigt fortgeschrittene Verwendungsmuster.
"""

import json
from pathlib import Path
from pdf_parser import PDFParser
from llm_extractor import extract_financials, chunk_text
from financial_calc import FinancialCalculator, format_currency


# ============================================================
# BEISPIEL 1: Batch-Verarbeitung von mehreren PDFs
# ============================================================

def batch_process_pdfs(pdf_directory: str) -> dict:
    """
    Verarbeite mehrere PDFs in einem Verzeichnis.
    
    Args:
        pdf_directory: Pfad zum Verzeichnis mit PDFs
    
    Returns:
        Dict mit Ergebnissen für alle PDFs
    """
    
    pdf_dir = Path(pdf_directory)
    results = {}
    
    for pdf_file in pdf_dir.glob("*.pdf"):
        print(f"Verarbeite: {pdf_file.name}")
        
        try:
            parser = PDFParser(str(pdf_file))
            text = parser.extract_text_all()
            parser.close()
            
            # Extrahiere mit LLM
            extracted = extract_financials(text, pdf_file.stem)
            
            # Berechne Kennzahlen
            calc = FinancialCalculator(extracted)
            results[pdf_file.stem] = calc.get_summary()
            
            print(f"  ✓ Erfolgreich verarbeitet")
            
        except Exception as e:
            print(f"  ✗ Fehler: {e}")
            results[pdf_file.stem] = {"error": str(e)}
    
    return results


def batch_example():
    """Beispiel für Batch-Verarbeitung."""
    
    print("=" * 60)
    print("BEISPIEL 1: Batch-Verarbeitung von PDFs")
    print("=" * 60)
    
    results = batch_process_pdfs("uploads")
    
    # Speichere Results
    output_file = "batch_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Ergebnisse gespeichert in: {output_file}")
    
    # Zeige Summary
    print("\nZusammenfassung:")
    for company, data in results.items():
        if "error" not in data:
            ebit = data.get("ebit")
            ebitda = data.get("ebitda")
            print(f"  {company:30} EBIT: {ebit:>15} EBITDA: {ebitda:>15}")


# ============================================================
# BEISPIEL 2: Vergleich mehrerer Unternehmen
# ============================================================

def compare_companies(results: dict):
    """
    Vergleiche mehrere Unternehmen basierend auf Kennzahlen.
    
    Args:
        results: Dict mit Ergebnissendelt der einzelnen Unternehmen
    """
    
    print("\n" + "=" * 60)
    print("BEISPIEL 2: Unternehmensvergleich")
    print("=" * 60)
    
    # Sammle Daten
    comparison = {}
    
    for company, data in results.items():
        if "error" in data:
            continue
        
        comparison[company] = {
            "ebit": data.get("ebit"),
            "ebitda": data.get("ebitda"),
            "net_profit": data.get("net_profit"),
            "employees": data.get("employees"),
        }
    
    # Berechne Pro-Kopf Metriken
    print("\nEBIT pro Mitarbeiter:")
    for company, metrics in comparison.items():
        if metrics["ebit"] and metrics["employees"]:
            ebit_per_employee = metrics["ebit"] / metrics["employees"]
            print(f"  {company:30} {ebit_per_employee:>15.2f} EUR")
    
    print("\nEBITDA pro Mitarbeiter:")
    for company, metrics in comparison.items():
        if metrics["ebitda"] and metrics["employees"]:
            ebitda_per_employee = metrics["ebitda"] / metrics["employees"]
            print(f"  {company:30} {ebitda_per_employee:>15.2f} EUR")


# ============================================================
# BEISPIEL 3: Erweiterte Analysen
# ============================================================

def analyze_profitability(results: dict):
    """
    Analysiere Rentabilität und Margen.
    
    Args:
        results: Berechnete Ergebnisse
    """
    
    print("\n" + "=" * 60)
    print("BEISPIEL 3: Rentabilitätsanalyse")
    print("=" * 60)
    
    ebit = results.get("ebit", {}).get("value")
    ebitda = results.get("ebitda", {}).get("value")
    net_profit = results.get("net_profit", {}).get("value")
    depreciation = results.get("depreciation", {}).get("value")
    
    if ebit and depreciation:
        dep_ratio = (depreciation / ebit) * 100
        print(f"\nAbschreibungsquote (Depreciation/EBIT): {dep_ratio:.2f}%")
    
    if ebitda and ebit:
        margin = ((ebitda - ebit) / ebitda) * 100
        print(f"Abschreibungenmarge (Depreciation/EBITDA): {margin:.2f}%")
    
    if net_profit and ebit:
        tax_rate = ((ebit - net_profit) / ebit) * 100
        print(f"Effektive Steuerlast: {tax_rate:.2f}%")


# ============================================================
# BEISPIEL 4: Manuelle Extraktion mit Verarbeitung
# ============================================================

def manual_extraction_with_debugging(pdf_path: str):
    """
    Sehr manuelle Extraktion mit Debug-Output.
    Hilfreich zur Fehlerbehebung.
    """
    
    print("\n" + "=" * 60)
    print("BEISPIEL 4: Manuelle Extraktion mit Debug")
    print("=" * 60)
    
    # Schritt 1: PDF laden
    print("\n[1] Lade PDF...")
    parser = PDFParser(pdf_path)
    print(f"    Seiten: {parser.num_pages}")
    
    # Schritt 2: Text extrahieren
    print("[2] Extrahiere Text...")
    text = parser.extract_text_all()
    print(f"    Länge: {len(text)} Zeichen")
    
    # Schritt 3: Zeige First Chunk
    print("[3] Zeige First Chunk (erste 500 Zeichen)...")
    first_chunk = text[:500]
    print("    " + first_chunk.replace("\n", "\n    "))
    
    # Schritt 4: Chunking
    print("[4] Teile in Chunks auf...")
    chunks = chunk_text(text, chunk_size=3000, overlap=300)
    print(f"    Anzahl Chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"      Chunk {i+1}: {len(chunk)} Zeichen")
    
    # Schritt 5: Extrahiere
    print("[5] Extrahiere mit LLM...")
    results = extract_financials(text, "DebugCompany")
    
    # Schritt 6: Zeige Zwischenergebnisse
    print("[6] Extraktions-Ergebnisse:")
    for metric, data in results.items():
        found = "✓" if data.get("found") else "✗"
        value = data.get("value", "N/A")
        print(f"    {found} {metric:20} = {value}")
    
    # Schritt 7: Berechne
    print("[7] Berechne Kennzahlen...")
    calc = FinancialCalculator(results)
    final = calc.get_all_calculations()
    
    print(f"    EBIT: {final['ebit']['value']} ({final['ebit']['method']})")
    print(f"    EBITDA: {final['ebitda']['value']} ({final['ebitda']['method']})")
    
    # Schritt 8: Speichere Outputs
    print("[8] Speichere Ergebnisse...")
    
    with open("debug_extraction.json", "w") as f:
        json.dump({
            "extracted": results,
            "calculated": final,
        }, f, indent=2, default=str)
    
    print("    ✓ In debug_extraction.json gespeichert")
    
    parser.close()


# ============================================================
# BEISPIEL 5: Custom LLM Prompt
# ============================================================

def custom_extraction_with_different_prompt(text: str):
    """
    Zeigt wie man Custom Prompts für spezifische Fälle nutzt.
    """
    
    from llm_extractor import call_ollama_api, parse_json_response
    
    print("\n" + "=" * 60)
    print("BEISPIEL 5: Custom LLM Prompt")
    print("=" * 60)
    
    # Custom Prompt für spezific Industrie
    custom_prompt = f"""
    Analysiere den folgenden Text aus einem Jahresabschluss einer 
    Produktionsunternehmen und extrahiere:
    
    1. Rohstoffkosten (Raw Materials)
    2. Lagerbestände (Inventory)
    3. Leasing-Verpflichtungen (Lease Obligations)
    
    ANTWORTE NUR MIT JSON:
    {{
      "raw_materials": <Zahl oder null>,
      "inventory": <Zahl oder null>,
      "lease_obligations": <Zahl oder null>
    }}
    
    TEXT:
    {text[:2000]}
    """
    
    print("Sende Custom Prompt an LLM...")
    response = call_ollama_api(custom_prompt)
    
    if response:
        parsed = parse_json_response(response)
        print(f"Ergebnis:")
        print(json.dumps(parsed, indent=2, default=str))
    else:
        print("Keine Antwort vom LLM")


# ============================================================
# BEISPIEL 6: Datenspeicherung und Versioning
# ============================================================

def save_with_versioning(company_name: str, data: dict):
    """
    Speichere Daten mit Versionierung.
    """
    
    from datetime import datetime
    
    print("\n" + "=" * 60)
    print("BEISPIEL 6: Versionierte Speicherung")
    print("=" * 60)
    
    # Erstelle Verzeichnis
    data_dir = Path("versioned_data") / company_name
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Speichere mit Zeitstempel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = data_dir / f"analysis_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✓ Gespeichert: {filename}")
    
    # Zähle Versionen
    versions = list(data_dir.glob("analysis_*.json"))
    print(f"  Gesamt Versionen: {len(versions)}")


# ============================================================
# HAUPTEINSTIEG
# ============================================================

if __name__ == "__main__":
    
    print("""
    🧪 Financial Cockpit - Erweiterte Beispiele
    
    Dieses Script zeigt fortgeschrittene Verwendungsmuster.
    Uncomment die Beispiele die du ausführen möchtest!
    """)
    
    # Uncomment zum Ausführen:
    
    # batch_example()
    
    # Für Vergleich:
    # results = batch_process_pdfs("uploads")
    # compare_companies(results)
    # if results:
    #     first_company_data = list(results.values())[0]
    #     analyze_profitability(first_company_data)
    
    # Für Debug:
    # manual_extraction_with_debugging("sample.pdf")
    
    # Für Custom Prompts:
    # with open("sample.txt", "r") as f:
    #     text = f.read()
    # custom_extraction_with_different_prompt(text)
    
    print("\n📝 Siehe den Code für Beispiele zum Uncomment!")
