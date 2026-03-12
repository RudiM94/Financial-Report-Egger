"""
Berechnungslogik für Finanzkennzahlen.
EBIT und EBITDA werden hier berechnet, nicht vom LLM!
"""

import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """Berechnet Finanzkennzahlen aus extrahierten Basisdaten."""
    
    def __init__(self, extracted_data: Dict):
        """
        Initialisiere Calculator mit extrahierten Daten vom LLM.
        
        Args:
            extracted_data: Dict mit Keys: operating_profit, net_profit, taxes, 
                           interest, depreciation, employees
        """
        self.data = extracted_data
        self.calculations = {}
        self.calculation_notes = {}
    
    def get_value(self, key: str) -> Optional[float]:
        """
        Hole einen Wert aus den extrahierten Daten.
        
        Args:
            key: Key im extracted_data
        
        Returns:
            Der numerische Wert oder None
        """
        if key in self.data and self.data[key].get("found"):
            return self.data[key].get("value")
        return None
    
    def calculate_ebit(self) -> Tuple[Optional[float], str]:
        """
        Berechne EBIT (Earnings Before Interest and Taxes).
        
        Prioritäts-Logik:
        1. Wenn "Betriebsergebnis" direkt gefunden wurde, nutze das
        2. Sonst berechne: EBIT = Net Profit + Taxes + Interest
        
        Returns:
            Tuple (Wert, Berechnungsmethode)
        """
        # Fall 1: Direkter Betriebsergebnis
        operating_profit = self.get_value("operating_profit")
        if operating_profit is not None:
            self.calculations["ebit"] = operating_profit
            self.calculation_notes["ebit"] = "Betriebsergebnis direkt gefunden"
            return operating_profit, "direct"
        
        # Fall 2: Berechnung aus Basis-Komponenten
        net_profit = self.get_value("net_profit")
        taxes = self.get_value("taxes")
        interest = self.get_value("interest")
        
        # Berechnung: EBIT = Jahresüberschuss + Steuern + Zinsen
        # Logik: NetProfit = (EBIT - Interest) - Taxes
        #        => EBIT = NetProfit + Taxes + Interest
        
        if net_profit is not None and taxes is not None and interest is not None:
            ebit = net_profit + taxes + interest
            self.calculations["ebit"] = ebit
            note = f"Berechnet aus: Jahresüberschuss ({net_profit:,.0f}) + Steuern ({taxes:,.0f}) + Zinsen ({interest:,.0f})"
            self.calculation_notes["ebit"] = note
            logger.info(f"EBIT berechnet: {ebit:,.0f}")
            return ebit, "calculated"
        
        # Fall 3: Teilweise Berechnung möglich
        if net_profit is not None and taxes is not None:
            # Wenn nur Interest fehlt, schätze mit 0
            interest_value = interest if interest is not None else 0
            ebit = net_profit + taxes + interest_value
            self.calculations["ebit"] = ebit
            note = f"Berechnet (partiell): Jahresüberschuss + Steuern + Zinsen (geschätzt: {interest_value:,.0f})"
            self.calculation_notes["ebit"] = note
            logger.warning(f"EBIT partiell berechnet (Zinsaufwand fehlend): {ebit:,.0f}")
            return ebit, "calculated_partial"
        
        self.calculations["ebit"] = None
        self.calculation_notes["ebit"] = "Nicht genug Daten zur EBIT-Berechnung"
        logger.warning("EBIT konnte nicht berechnet werden - zu viele fehlende Werte")
        return None, "not_calculated"
    
    def calculate_ebitda(self) -> Tuple[Optional[float], str]:
        """
        Berechne EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization).
        
        Formel: EBITDA = EBIT + Depreciation (Abschreibungen)
        
        Returns:
            Tuple (Wert, Berechnungsmethode)
        """
        # Zuerst EBIT berechnen
        ebit, ebit_method = self.calculate_ebit()
        depreciation = self.get_value("depreciation")
        
        if ebit is None:
            self.calculations["ebitda"] = None
            self.calculation_notes["ebitda"] = "EBITDA kann nicht berechnet werden - EBIT fehlend"
            return None, "not_calculated"
        
        if depreciation is None:
            # Wenn Depreciation fehlt, nutze EBIT = EBITDA
            self.calculations["ebitda"] = ebit
            self.calculation_notes["ebitda"] = f"Berechnet als EBIT (Abschreibungen fehlend): {ebit:,.0f}"
            logger.warning("EBITDA = EBIT (Abschreibungen nicht extrahiert)")
            return ebit, "calculated_without_depreciation"
        
        ebitda = ebit + depreciation
        self.calculations["ebitda"] = ebitda
        note = f"Berechnet: EBIT ({ebit:,.0f}) + Abschreibungen ({depreciation:,.0f})"
        self.calculation_notes["ebitda"] = note
        logger.info(f"EBITDA berechnet: {ebitda:,.0f}")
        
        return ebitda, "calculated"
    
    def get_all_calculations(self) -> Dict:
        """
        Führe alle Berechnungen durch und gebe Results zurück.
        
        Returns:
            Dict mit allen berechneten Werten und Details
        """
        # Berechne EBIT und EBITDA
        ebit, ebit_method = self.calculate_ebit()
        ebitda, ebitda_method = self.calculate_ebitda()
        
        # Hole direkt extrahierte Werte
        result = {
            # Direkt extrahierte Werte
            "operating_profit": {
                "value": self.get_value("operating_profit"),
                "found": self.data.get("operating_profit", {}).get("found", False),
                "context": self.data.get("operating_profit", {}).get("context", ""),
            },
            "net_profit": {
                "value": self.get_value("net_profit"),
                "found": self.data.get("net_profit", {}).get("found", False),
                "context": self.data.get("net_profit", {}).get("context", ""),
            },
            "taxes": {
                "value": self.get_value("taxes"),
                "found": self.data.get("taxes", {}).get("found", False),
                "context": self.data.get("taxes", {}).get("context", ""),
            },
            "interest": {
                "value": self.get_value("interest"),
                "found": self.data.get("interest", {}).get("found", False),
                "context": self.data.get("interest", {}).get("context", ""),
            },
            "depreciation": {
                "value": self.get_value("depreciation"),
                "found": self.data.get("depreciation", {}).get("found", False),
                "context": self.data.get("depreciation", {}).get("context", ""),
            },
            "employees": {
                "value": self.get_value("employees"),
                "found": self.data.get("employees", {}).get("found", False),
                "unit": self.data.get("employees", {}).get("unit", "number"),
                "context": self.data.get("employees", {}).get("context", ""),
            },
            # Berechnete Werte
            "ebit": {
                "value": ebit,
                "method": ebit_method,
                "note": self.calculation_notes.get("ebit", ""),
                "found": ebit is not None,
            },
            "ebitda": {
                "value": ebitda,
                "method": ebitda_method,
                "note": self.calculation_notes.get("ebitda", ""),
                "found": ebitda is not None,
            },
        }
        
        return result
    
    def get_summary(self) -> Dict:
        """
        Gebe eine Zusammenfassung der wichtigsten KPIs.
        
        Returns:
            Dict mit summary data für Dashboard
        """
        all_data = self.get_all_calculations()
        
        return {
            "revenue": self.get_value("operating_profit"),  # Vereinfachung
            "operating_profit": all_data["operating_profit"]["value"],
            "ebit": all_data["ebit"]["value"],
            "ebitda": all_data["ebitda"]["value"],
            "net_profit": all_data["net_profit"]["value"],
            "taxes": all_data["taxes"]["value"],
            "interest": all_data["interest"]["value"],
            "depreciation": all_data["depreciation"]["value"],
            "employees": all_data["employees"]["value"],
            "ebit_method": all_data["ebit"]["method"],
            "ebitda_method": all_data["ebitda"]["method"],
        }


def calculate_profitability_metrics(net_profit: float, revenue: Optional[float]) -> Dict:
    """
    Berechne Profitabilitätskennzahlen.
    
    Args:
        net_profit: Jahresüberschuss
        revenue: Umsatz (Optional)
    
    Returns:
        Dict mit berechneten Kennzahlen
    """
    metrics = {}
    
    if revenue and revenue != 0:
        metrics["profit_margin"] = (net_profit / revenue) * 100
    
    return metrics


def format_currency(value: Optional[float], currency: str = "EUR", decimals: int = 0) -> str:
    """
    Formatiere einen Wert als Währung.
    
    Args:
        value: Wert zum Formatieren
        currency: Währungscode
        decimals: Dezimalstellen
    
    Returns:
        Formatierter String
    """
    if value is None:
        return "N/A"
    
    if decimals == 0:
        return f"{value:,.0f} {currency}"
    else:
        return f"{value:,.{decimals}f} {currency}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test-Daten
    test_data = {
        "operating_profit": {"value": None, "found": False},
        "net_profit": {"value": 1000000, "found": True, "context": "Jahresüberschuss"},
        "taxes": {"value": 300000, "found": True, "context": "Steuern"},
        "interest": {"value": 150000, "found": True, "context": "Zinsaufwand"},
        "depreciation": {"value": 500000, "found": True, "context": "Abschreibungen"},
        "employees": {"value": 250, "found": True, "unit": "number"},
    }
    
    calc = FinancialCalculator(test_data)
    results = calc.get_all_calculations()
    
    print("Test Calculations:")
    print(f"  EBIT: {results['ebit']['value']:,.0f} ({results['ebit']['method']})")
    print(f"  EBITDA: {results['ebitda']['value']:,.0f} ({results['ebitda']['method']})")
    print(f"  Note: {results['ebit']['note']}")
