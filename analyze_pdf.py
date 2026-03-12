from pdf_parser import PDFParser

# Analysiere die Desktop-PDF
text = PDFParser('/Users/luca/Desktop/Adolf Darbo1.pdf').extract_text_all()

# Suche nach Schlüsselwörtern
print("🔍 ANALYSE DER PDF:\n")

# Suche Jahresüberschuss
lines_with_result = [l for l in text.split('\n') if 'jahresergebnis' in l.lower() or 'jahresüberschuss' in l.lower() or 'gewinn' in l.lower()]
print(f"📊 Jahresüberschuss/Gewinn Zeilen ({len(lines_with_result)}):")
for i, line in enumerate(lines_with_result[:3], 1):
    print(f"  {i}. {line[:100]}")

# Suche Bilanzsumme
lines_with_balance = [l for l in text.split('\n') if 'bilanzsumme' in l.lower()]
print(f"\n💰 Bilanzsumme Zeilen ({len(lines_with_balance)}):")
for i, line in enumerate(lines_with_balance[:3], 1):
    print(f"  {i}. {line[:100]}")

# Suche Mitarbeiter
lines_with_employees = [l for l in text.split('\n') if 'mitarbeiter' in l.lower() or 'personal' in l.lower()]
print(f"\n👥 Mitarbeiter Zeilen ({len(lines_with_employees)}):")
for i, line in enumerate(lines_with_employees[:3], 1):
    print(f"  {i}. {line[:100]}")

# Show first 200 chars
print(f"\n📄 Erste 500 Zeichen:")
print(text[:500])
