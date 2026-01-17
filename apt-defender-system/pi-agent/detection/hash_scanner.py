"""
File Hash Scanner - Check files against malware databases
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, List
import httpx

logger = logging.getLogger(__name__)

class HashScanner:
    """SHA256 hash scanner with VirusTotal integration"""
    
    def __init__(self, vt_api_key: Optional[str] = None):
        self.vt_api_key = vt_api_key
        self.known_malware_hashes = set()
        self._load_malware_database()
    
    def _load_malware_database(self):
        """Load known malware hashes from local database"""
        # TODO: Load from file or database
        # Format: SHA256 hashes, one per line
        logger.info("Loaded malware hash database")
    
    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read in 64kb chunks
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def check_local_database(self, file_hash: str) -> bool:
        """Check if hash exists in local malware database"""
        return file_hash.lower() in self.known_malware_hashes
    
    async def check_virustotal(self, file_hash: str) -> Dict:
        """Check hash against VirusTotal API"""
        if not self.vt_api_key:
            return {"error": "No VirusTotal API key configured"}
        
        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {"x-apikey": self.vt_api_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    
                    return {
                        "found": True,
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "harmless": stats.get("harmless", 0),
                        "undetected": stats.get("undetected", 0)
                    }
                elif response.status_code == 404:
                    return {"found": False}
                else:
                    return {"error": f"VirusTotal API error: {response.status_code}"}
        
        except Exception as e:
            logger.error(f"VirusTotal API error: {e}")
            return {"error": str(e)}
    
    async def scan_file(self, file_path: str) -> Dict:
        """
        Scan a file and return threat assessment
        
        Returns:
            {
                "hash": "sha256...",
                "malicious": True/False,
                "source": "local_db" | "virustotal" | "clean",
                "details": {...}
            }
        """
        file_hash = self.calculate_sha256(file_path)
        
        if not file_hash:
            return {"error": "Could not hash file"}
        
        # Check local database first (fast)
        if self.check_local_database(file_hash):
            return {
                "hash": file_hash,
                "malicious": True,
                "source": "local_db",
                "explanation": "File matches known malware signature"
            }
        
        # Check VirusTotal if available
        if self.vt_api_key:
            vt_result = await self.check_virustotal(file_hash)
            
            if vt_result.get("found") and vt_result.get("malicious", 0) > 5:
                return {
                    "hash": file_hash,
                    "malicious": True,
                    "source": "virustotal",
                    "explanation": f"Detected by {vt_result['malicious']} antivirus engines",
                    "details": vt_result
                }
        
        # File appears clean
        return {
            "hash": file_hash,
            "malicious": False,
            "source": "clean"
        }
    
    async def scan_directory(self, directory: str, extensions: List[str] = None) -> List[Dict]:
        """
        Scan all files in directory
        
        Args:
            directory: Path to scan
            extensions: List of file extensions to scan (e.g., ['.exe', '.dll'])
        """
        results = []
        target_path = Path(directory)
        
        if not target_path.exists():
            logger.error(f"Directory not found: {directory}")
            return results
        
        # Scan files
        for file_path in target_path.rglob('*'):
            if file_path.is_file():
                # Filter by extension if specified
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                result = await self.scan_file(str(file_path))
                result['path'] = str(file_path)
                results.append(result)
        
        return results
