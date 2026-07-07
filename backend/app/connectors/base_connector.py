# Base Connector.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)

class BaseConnector(ABC): 
    def __init__(self, name: str, base_url: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.is_connected = False
        self.metadata = {
            "name": name,
            "base_url": base_url,
            "last_fetch": None,
            "records_fetched": 0,
        }
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def fetch(self, query: Optional[str] = None, **kwargs) -> List[Dict]:
        pass
    
    @abstractmethod
    def validate(self, data: List[Dict]) -> bool:
        pass
    
    @abstractmethod
    def transform(self, data: List[Dict]) -> List[Dict]:
        pass
    
    async def ingest(self, query: Optional[str] = None, **kwargs) -> Dict:
        try:
            connected = await self.connect()
            if not connected:
                raise ConnectionError(f"Failed to connect to {self.name}")
            
            raw_data = await self.fetch(query, **kwargs)
            
            if not self.validate(raw_data):
                raise ValueError(f"Data validation failed for {self.name}")
            
            transformed_data = self.transform(raw_data)
            
            self.metadata["last_fetch"] = __import__('datetime').datetime.utcnow().isoformat()
            self.metadata["records_fetched"] = len(transformed_data)
            
            logger.info("data_ingested", connector=self.name, records=len(transformed_data))
            
            return {
                "status": "success",
                "connector": self.name,
                "records": len(transformed_data),
                "data": transformed_data,
                "metadata": self.metadata,
            }
            
        except Exception as e:
            logger.error("ingestion_failed", connector=self.name, error=str(e))
            return {
                "status": "failed",
                "connector": self.name,
                "error": str(e),
                "metadata": self.metadata,
            }
    
    # TODO: Add connection pooling
    # TODO: Add retry with exponential backoff
    # TODO: Add response caching