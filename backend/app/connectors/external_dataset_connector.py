# External Dataset Connector.

from typing import Dict, List, Optional

from app.connectors.base_connector import BaseConnector
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ExternalDatasetConnector(BaseConnector):
    
    def __init__(self):
        super().__init__("external_dataset", None)
        self.connectors = {}
    
    def register_connector(self, name: str, connector: BaseConnector) -> None:
        self.connectors[name] = connector
        logger.info("connector_registered", name=name)
    
    async def connect(self) -> bool:
        results = []
        for name, connector in self.connectors.items():
            try:
                connected = await connector.connect()
                results.append(connected)
            except Exception as e:
                logger.error("connector_connection_error", name=name, error=str(e))
                results.append(False)
        
        self.is_connected = any(results)
        return self.is_connected
    
    async def fetch(self, source: str = None, **kwargs) -> List[Dict]:
        all_data = []
        
        sources = [source] if source else self.connectors.keys()
        
        for src in sources:
            if src not in self.connectors:
                logger.warning("unknown_source", source=src)
                continue
            
            try:
                connector = self.connectors[src]
                result = await connector.ingest(**kwargs)
                if result["status"] == "success":
                    all_data.extend(result["data"])
            except Exception as e:
                logger.error("source_fetch_error", source=src, error=str(e))
        
        return all_data
    
    def validate(self, data: List[Dict]) -> bool:
        return len(data) > 0
    
    def transform(self, data: List[Dict]) -> List[Dict]:
        return data
    
    # TODO: Add FSD Kenya integration
    # TODO: Add alternative data provider connections
    # TODO: Add dataset quality scoring