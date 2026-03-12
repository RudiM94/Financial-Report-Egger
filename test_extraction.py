#!/usr/bin/env python3
"""Test script for LLM extraction quality."""

import sys
sys.path.insert(0, '.')

from pdf_parser import PDFParser
from llm_extractor import extract_financials, call_ollama_api, build_extraction_prompt
import json

print("📄 Test LLM Extraction Quality\n")

# Lade PDF
pdf_file = "180425_Lenzing+AG+2024-2.pdf"
print(f"📖 Loading: {pdf_file}")
try:
    pdf = PDFParser(pdf_file)
    full_text = pdf.extract_text_all()
    print(f"✓ Loaded {len(full_text)} characters\n")
except FileNotFoundError:
    print(f"❌ File not found: {pdf_file}")
    sys.exit(1)

# Zeige erstes Stück des Textes
print("📝 First 600 chars of PDF:\n")
print(full_text[:600])
print("\n" + "="*70 + "\n")

# Teste manuelle Extraktion eines Chunks
print("🔍 Testing LLM extraction on first chunk...\n")

chunk = full_text[:3000]
prompt = build_extraction_prompt(chunk, ["operating_profit", "net_profit", "taxes", "interest", "depreciation", "employees"])

print("Sending to Ollama...")
response = call_ollama_api(prompt)

print("\n📋 Raw LLM Response:")
print(response[:500] if response else "NO RESPONSE")
print("\n" + "="*70 + "\n")

# Jetzt teste die volle Extraktion
print("🔄 Full extraction with combine...\n")
results = extract_financials(full_text, "Lenzing AG")

print("📊 Final Results:")
print(json.dumps(results, indent=2, ensure_ascii=False))
