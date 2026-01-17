"""
Helper Service Client - Interface to communicate with PC Helper service
"""
import httpx
import logging
from typing import Dict, List, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class HelperClient:
    """Client for communicating with Helper service on target PC"""
    
    def __init__(self, helper_url: str, cert_path: Optional[str] = None):
        """
        Args:
            helper_url: Base URL of helper service (e.g., https://192.168.1.100:7890)
            cert_path: Path to client certificate for mTLS
        """
        self.base_url = helper_url.rstrip('/')
        self.cert_path = cert_path
        self.timeout = settings.helper_timeout_seconds
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request to Helper service"""
        url = f"{self.base_url}/v1{endpoint}"
        
        # Prepare mTLS certificates
        # In production, these should be loaded from settings
        cert = (settings.ssl_certfile, settings.ssl_keyfile)
        verify = False # For self-signed certs without a root CA in system store
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                cert=cert,
                verify=verify 
            ) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Helper service: {url}")
            raise Exception("Device is not responding")
        except httpx.HTTPStatusError as e:
            logger.error(f"Helper service error: {e}")
            raise Exception(f"Device error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Helper service connection error: {e}")
            raise Exception("Cannot reach device")
    
    async def health_check(self) -> Dict:
        """Check if Helper service is reachable"""
        return await self._request("GET", "/health")
    
    async def get_processes(self) -> List[Dict]:
        """Get list of running processes"""
        result = await self._request("GET", "/processes")
        return result.get('processes', [])
    
    async def get_file_hash(self, file_path: str) -> str:
        """Get SHA256 hash of file"""
        import base64
        encoded_path = base64.b64encode(file_path.encode()).decode()
        result = await self._request("GET", f"/files/hash?path={encoded_path}")
        return result.get('sha256', '')
    
    async def kill_process(self, pid: int) -> bool:
        """Kill a process by PID"""
        result = await self._request("POST", "/process/kill", json={"pid": pid})
        return result.get('success', False)
    
    async def quarantine_file(self, file_path: str, reason: str = "Threat detected") -> Dict:
        """Move file to quarantine"""
        result = await self._request("POST", "/file/quarantine", json={
            "path": file_path,
            "reason": reason
        })
        return result
    
    async def disable_network(self) -> bool:
        """Disable all network adapters"""
        result = await self._request("POST", "/network/disable", json={})
        return result.get('success', False)
    
    async def lock_system(self) -> bool:
        """Lock the system"""
        result = await self._request("POST", "/system/lock", json={})
        return result.get('success', False)
    
    async def shutdown_system(self, delay_seconds: int = 60) -> bool:
        """Shutdown the system with delay"""
        result = await self._request("POST", "/system/shutdown", json={
            "delay_seconds": delay_seconds
        })
        return result.get('success', False)
    
    async def get_persistence_entries(self) -> List[Dict]:
        """Get persistence mechanisms (autoruns, scheduled tasks, etc.)"""
        result = await self._request("GET", "/persistence")
        return result.get('entries', [])
    
    async def get_network_connections(self) -> List[Dict]:
        """Get active network connections"""
        result = await self._request("GET", "/network/connections")
        return result.get('connections', [])
