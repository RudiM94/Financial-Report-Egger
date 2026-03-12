"""
PDF-Verarbeitung mit PyMuPDF (fitz).
Extrahiert Text aus Jahresabschlüssen für die LLM-Analyse.
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser für PDF-Dokumente mittels PyMuPDF."""
    
    def __init__(self, pdf_path: str):
        """
        Initialisiere PDF Parser.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
        """
        self.pdf_path = Path(pdf_path)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")
        
        try:
            self.doc = fitz.open(self.pdf_path)
            self.num_pages = len(self.doc)
            logger.info(f"PDF geöffnet: {self.pdf_path.name} ({self.num_pages} Seiten)")
        except Exception as e:
            logger.error(f"Fehler beim Öffnen der PDF: {e}")
            raise
    
    def extract_text_all(self) -> str:
        """
        Extrahiere Text aus allen Seiten.
        
        Returns:
            Kompletter Text aus der PDF
        """
        text = ""
        
        for page_num in range(self.num_pages):
            try:
                page = self.doc[page_num]
                page_text = page.get_text("text")
                
                # Füge Seitennummer hinzu für Referenzierung
                text += f"\n--- Seite {page_num + 1} ---\n"
                text += page_text
                
            except Exception as e:
                logger.warning(f"Fehler bei Seite {page_num + 1}: {e}")
        
        return text
    
    def extract_text_range(self, start_page: int = 0, end_page: Optional[int] = None) -> str:
        """
        Extrahiere Text aus einem Seitenbereich.
        
        Args:
            start_page: Startseite (0-indexiert)
            end_page: Endseite (0-indexiert, inklusive). None = letzte Seite
        
        Returns:
            Text aus dem Seitenbereich
        """
        if end_page is None:
            end_page = self.num_pages - 1
        
        if start_page < 0 or end_page >= self.num_pages or start_page > end_page:
            raise ValueError(f"Ungültige Seitenbereich: {start_page}-{end_page}")
        
        text = ""
        
        for page_num in range(start_page, end_page + 1):
            try:
                page = self.doc[page_num]
                page_text = page.get_text("text")
                text += f"\n--- Seite {page_num + 1} ---\n"
                text += page_text
            except Exception as e:
                logger.warning(f"Fehler bei Seite {page_num + 1}: {e}")
        
        return text
    
    def extract_structured_data(self) -> dict:
        """
        Extrahiere strukturierte Informationen aus PDF.
        
        Returns:
            Dict mit Metadaten und Textinformation
        """
        metadata = self.doc.metadata
        
        return {
            "filename": self.pdf_path.name,
            "num_pages": self.num_pages,
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
        }
    
    def extract_text_by_pattern(self, search_terms: list) -> dict:
        """
        Extrahiere Textumgebung um spezifische Begriffe.
        
        Args:
            search_terms: Liste von Suchbegriffen
        
        Returns:
            Dict mit Fundstellen und Kontext
        """
        results = {}
        text_all = self.extract_text_all()
        
        for term in search_terms:
            findings = []
            text_lower = text_all.lower()
            term_lower = term.lower()
            
            # Finde alle Vorkommen
            start_idx = 0
            while True:
                idx = text_lower.find(term_lower, start_idx)
                if idx == -1:
                    break
                
                # Extrahiere Kontext (±100 Zeichen)
                context_start = max(0, idx - 100)
                context_end = min(len(text_all), idx + len(term) + 100)
                context = text_all[context_start:context_end].replace("\n", " ")
                
                findings.append({
                    "position": idx,
                    "context": context
                })
                
                start_idx = idx + len(term)
            
            if findings:
                results[term] = findings
        
        return results
    
    def get_page_content(self, page_num: int) -> Tuple[str, dict]:
        """
        Hole den Inhalt einer bestimmten Seite.
        
        Args:
            page_num: Seitennummer (0-indexiert)
        
        Returns:
            Tuple mit (Text, Metadaten der Seite)
        """
        if page_num < 0 or page_num >= self.num_pages:
            raise ValueError(f"Seitennummer außerhalb Bereich: {page_num}")
        
        page = self.doc[page_num]
        text = page.get_text("text")
        
        # Extrahiere Seitent-Metadaten
        rect = page.rect
        
        return text, {
            "page_num": page_num + 1,
            "width": rect.width,
            "height": rect.height,
            "rotation": page.rotation,
        }
    
    def close(self):
        """Schließe das PDF-Dokument."""
        if hasattr(self, 'doc'):
            self.doc.close()
            logger.info(f"PDF geschlossen: {self.pdf_path.name}")
    
    def __enter__(self):
        """Context Manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager support."""
        self.close()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Convenience-Funktion zum Extrahieren von Text aus einer PDF.
    
    Args:
        pdf_path: Pfad zur PDF-Datei
    
    Returns:
        Kompletter Text aus der PDF
    """
    with PDFParser(pdf_path) as parser:
        return parser.extract_text_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Beispiel-Verwendung
    pdf_file = "sample.pdf"
    
    try:
        parser = PDFParser(pdf_file)
        print(f"✓ PDF geladen: {parser.num_pages} Seiten")
        
        # Extrahiere Text
        text = parser.extract_text_all()
        print(f"✓ Text extrahiert: {len(text)} Zeichen")
        
        # Metadaten
        meta = parser.extract_structured_data()
        print(f"✓ Metadaten: {meta}")
        
        parser.close()
        
    except Exception as e:
        print(f"✗ Fehler: {e}")
