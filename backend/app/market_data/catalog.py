from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StockDefinition:
    company_name: str
    sector: str
    exchange: str
    demo_price: float


# A deliberately curated, liquid cross-border universe. Canadian symbols use the
# Yahoo Finance suffixes expected by the existing market-data provider.
STOCK_CATALOG: dict[str, StockDefinition] = {
    # NASDAQ
    "AAPL": StockDefinition("Apple Inc.", "Technology", "NASDAQ", 222.0),
    "MSFT": StockDefinition("Microsoft Corp.", "Technology", "NASDAQ", 426.0),
    "NVDA": StockDefinition("NVIDIA Corp.", "Semiconductors", "NASDAQ", 181.0),
    "GOOG": StockDefinition("Alphabet Inc. Class C", "Communication Services", "NASDAQ", 205.0),
    "AMZN": StockDefinition("Amazon.com Inc.", "Consumer Cyclical", "NASDAQ", 228.0),
    "META": StockDefinition("Meta Platforms Inc.", "Communication Services", "NASDAQ", 612.0),
    "TSLA": StockDefinition("Tesla Inc.", "Automotive", "NASDAQ", 339.0),
    "AVGO": StockDefinition("Broadcom Inc.", "Semiconductors", "NASDAQ", 195.0),
    "AMD": StockDefinition("Advanced Micro Devices Inc.", "Semiconductors", "NASDAQ", 158.0),
    "COST": StockDefinition("Costco Wholesale Corp.", "Consumer Defensive", "NASDAQ", 980.0),
    "NFLX": StockDefinition("Netflix Inc.", "Communication Services", "NASDAQ", 118.0),
    "ADBE": StockDefinition("Adobe Inc.", "Software", "NASDAQ", 355.0),
    "CSCO": StockDefinition("Cisco Systems Inc.", "Technology", "NASDAQ", 68.0),
    "INTC": StockDefinition("Intel Corp.", "Semiconductors", "NASDAQ", 35.0),
    "QCOM": StockDefinition("Qualcomm Inc.", "Semiconductors", "NASDAQ", 168.0),
    "PEP": StockDefinition("PepsiCo Inc.", "Consumer Defensive", "NASDAQ", 148.0),
    "TMUS": StockDefinition("T-Mobile US Inc.", "Communication Services", "NASDAQ", 236.0),
    "QQQ": StockDefinition("Invesco QQQ Trust", "ETF", "NASDAQ", 570.0),
    # NYSE and NYSE Arca
    "JPM": StockDefinition("JPMorgan Chase & Co.", "Financial Services", "NYSE", 295.0),
    "V": StockDefinition("Visa Inc.", "Financial Services", "NYSE", 345.0),
    "MA": StockDefinition("Mastercard Inc.", "Financial Services", "NYSE", 560.0),
    "WMT": StockDefinition("Walmart Inc.", "Consumer Defensive", "NYSE", 104.0),
    "JNJ": StockDefinition("Johnson & Johnson", "Healthcare", "NYSE", 174.0),
    "XOM": StockDefinition("Exxon Mobil Corp.", "Energy", "NYSE", 116.0),
    "UNH": StockDefinition("UnitedHealth Group Inc.", "Healthcare", "NYSE", 365.0),
    "HD": StockDefinition("The Home Depot Inc.", "Consumer Cyclical", "NYSE", 405.0),
    "BAC": StockDefinition("Bank of America Corp.", "Financial Services", "NYSE", 51.0),
    "KO": StockDefinition("The Coca-Cola Co.", "Consumer Defensive", "NYSE", 70.0),
    "DIS": StockDefinition("The Walt Disney Co.", "Communication Services", "NYSE", 118.0),
    "NKE": StockDefinition("Nike Inc.", "Consumer Cyclical", "NYSE", 74.0),
    "CRM": StockDefinition("Salesforce Inc.", "Software", "NYSE", 255.0),
    "ORCL": StockDefinition("Oracle Corp.", "Software", "NYSE", 185.0),
    "IBM": StockDefinition("International Business Machines Corp.", "Technology", "NYSE", 265.0),
    "GE": StockDefinition("GE Aerospace", "Industrials", "NYSE", 285.0),
    "CAT": StockDefinition("Caterpillar Inc.", "Industrials", "NYSE", 425.0),
    "SPY": StockDefinition("SPDR S&P 500 ETF Trust", "ETF", "NYSE Arca", 649.0),
    # Toronto Stock Exchange (Yahoo suffix: .TO)
    "SHOP.TO": StockDefinition("Shopify Inc.", "Technology", "TSX", 156.0),
    "RY.TO": StockDefinition("Royal Bank of Canada", "Financial Services", "TSX", 205.0),
    "TD.TO": StockDefinition("Toronto-Dominion Bank", "Financial Services", "TSX", 115.0),
    "ENB.TO": StockDefinition("Enbridge Inc.", "Energy", "TSX", 66.0),
    "CNR.TO": StockDefinition("Canadian National Railway Co.", "Industrials", "TSX", 145.0),
    "CP.TO": StockDefinition("Canadian Pacific Kansas City Ltd.", "Industrials", "TSX", 112.0),
    "BMO.TO": StockDefinition("Bank of Montreal", "Financial Services", "TSX", 178.0),
    "BNS.TO": StockDefinition("Bank of Nova Scotia", "Financial Services", "TSX", 90.0),
    "CM.TO": StockDefinition("Canadian Imperial Bank of Commerce", "Financial Services", "TSX", 108.0),
    "SU.TO": StockDefinition("Suncor Energy Inc.", "Energy", "TSX", 58.0),
    "CNQ.TO": StockDefinition("Canadian Natural Resources Ltd.", "Energy", "TSX", 46.0),
    "TRI.TO": StockDefinition("Thomson Reuters Corp.", "Industrials", "TSX", 245.0),
    "MFC.TO": StockDefinition("Manulife Financial Corp.", "Financial Services", "TSX", 45.0),
    "WCN.TO": StockDefinition("Waste Connections Inc.", "Industrials", "TSX", 255.0),
    "CSU.TO": StockDefinition("Constellation Software Inc.", "Technology", "TSX", 5100.0),
    "ATD.TO": StockDefinition("Alimentation Couche-Tard Inc.", "Consumer Defensive", "TSX", 72.0),
    "ABX.TO": StockDefinition("Barrick Mining Corp.", "Basic Materials", "TSX", 29.0),
    "NTR.TO": StockDefinition("Nutrien Ltd.", "Basic Materials", "TSX", 78.0),
    "BAM.TO": StockDefinition("Brookfield Asset Management Ltd.", "Financial Services", "TSX", 76.0),
    "XIU.TO": StockDefinition("iShares S&P/TSX 60 Index ETF", "ETF", "TSX", 41.0),
    "HIVE.TO": StockDefinition("HIVE Digital Technologies Ltd.", "Technology", "TSX", 4.0),
    # TSX Venture Exchange (Yahoo suffix: .V)
    "PNG.V": StockDefinition("Kraken Robotics Inc.", "Industrials", "TSXV", 2.8),
    "NGEX.V": StockDefinition("NGEx Minerals Ltd.", "Basic Materials", "TSXV", 21.0),
    "FPX.V": StockDefinition("FPX Nickel Corp.", "Basic Materials", "TSXV", 0.45),
    "GPH.V": StockDefinition("Graphite One Inc.", "Basic Materials", "TSXV", 1.2),
    "FAN.V": StockDefinition("First Atlantic Nickel & Cobalt Corp.", "Basic Materials", "TSXV", 0.82),
    "WRLG.V": StockDefinition("West Red Lake Gold Mines Ltd.", "Basic Materials", "TSXV", 1.0),
    "GSVR.V": StockDefinition("Guanajuato Silver Company Ltd.", "Basic Materials", "TSXV", 0.35),
    "FLCN.V": StockDefinition("Falcon Energy Materials PLC", "Basic Materials", "TSXV", 0.98),
}

EXCHANGES = ("NASDAQ", "NYSE", "NYSE Arca", "TSX", "TSXV")
CORE_DEMO_SYMBOLS = ("AAPL", "MSFT", "NVDA", "GOOG", "AMZN", "META", "TSLA", "SPY")
