# World Bank Connector.
# This Fetches macroeconomic indicators from World Bank Open Data API.

from typing import Dict, List, Optional

import httpx

from app.config import settings
from app.connectors.base_connector import BaseConnector
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class WorldBankConnector(BaseConnector):
    def __init__(self):
        super().__init__("world_bank", settings.world_bank_api_url)
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def connect(self) -> bool:
        # Test API connectivity.
        try:
            response = await self.client.get(f"{self.base_url}/country/KE?format=json")
            self.is_connected = response.status_code == 200
            return self.is_connected
        except Exception as e:
            logger.error("world_bank_connection_error", error=str(e))
            return False
    
    async def fetch(
        self,
        indicator: str = "FP.CPI.TOTL.ZG",  # Inflation rate
        country: str = "KE",
        date_range: str = "2020:2024",
    ) -> List[Dict]:
        url = f"{self.base_url}/country/{country}/indicator/{indicator}"
        params = {
            "date": date_range,
            "format": "json",
            "per_page": 100,
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            # World Bank returns [metadata, data]
            if len(data) > 1 and isinstance(data[1], list):
                records = []
                for item in data[1]:
                    records.append({
                        "indicator": indicator,
                        "country": country,
                        "year": item.get("date"),
                        "value": item.get("value"),
                        "unit": item.get("unit", ""),
                    })
                return records
            
            return []
            
        except Exception as e:
            logger.error("world_bank_fetch_error", indicator=indicator, error=str(e))
            return []
    
    def validate(self, data: List[Dict]) -> bool:
        # Validate indicator data.
        if not data:
            return False
        return all("value" in d and d["value"] is not None for d in data)
    
    def transform(self, data: List[Dict]) -> List[Dict]:
        return [
            {
                "source": "world_bank",
                "indicator": d["indicator"],
                "country": d["country"],
                "year": int(d["year"]) if d.get("year") else None,
                "value": float(d["value"]) if d.get("value") else None,
                "metric_type": "macroeconomic",
                "fetched_at": __import__('datetime').datetime.utcnow().isoformat(),
            }
            for d in data
        ]
    
    async def get_kenya_indicators(self) -> Dict[str, List[Dict]]:
        indicators = {
            "inflation": "FP.CPI.TOTL.ZG",
            "gdp_growth": "NY.GDP.MKTP.KD.ZG",
            "unemployment": "SL.UEM.TOTL.ZS",
            "poverty_headcount": "SI.POV.NAHC",
            "financial_inclusion": "FX.OWN.TOTL.ZS",
        }
        
        results = {}
        for name, code in indicators.items():
            data = await self.fetch(indicator=code)
            results[name] = self.transform(data)
        
        return results
    
    # TODO: Add county-level data support
    # TODO: Add caching layer
    # TODO: Add time series interpolation