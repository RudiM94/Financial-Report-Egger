from pdf_parser import PDFParser
from llm_extractor import build_extraction_prompt, call_ollama_api, parse_json_response
import json

# Get the PDF
text = PDFParser('/Users/luca/Desktop/Adolf Darbo1.pdf').extract_text_all()

# Find the section with "3.1. Personal"
lines = text.split('\n')
personal_idx = -1
for i, line in enumerate(lines):
    if '3.1. Personal' in line:
        personal_idx = i
        break

if personal_idx >= 0:
    # Get context around Personal section (200 lines)
    chunk = '\n'.join(lines[personal_idx:personal_idx+20])
    print("📄 Test-Chunk mit Mitarbeiter-Section:\n")
    print(chunk)
    print("\n\n🚀 Sende an LLM...\n")
    
    prompt = build_extraction_prompt(chunk, ["employees"])
    response = call_ollama_api(prompt)
    
    if response:
        print("✅ LLM Response (first 300 chars):")
        print(response[:300])
        
        parsed = parse_json_response(response)
        if parsed:
            print("\n✅ Parsed JSON:")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
else:
    print("❌ Personal section not found")
