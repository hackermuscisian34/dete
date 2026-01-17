import asyncio
import logging
from supabase import create_client, Client
from config.settings import settings

logger = logging.getLogger("supabase_sync")

class SupabaseSync:
    def __init__(self):
        self.client: Client = None
        self.enabled = False
        
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                self.enabled = True
                logger.info("☁️ Cloud sync initialized (Supabase)")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
    
    async def sync_device_status(self, hostname: str, status: str, ip: str, os: str):
        """Upsert device status to cloud"""
        if not self.enabled: return

        try:
            data = {
                "hostname": hostname,
                "status": status,
                "ip_address": ip,
                "os": os,
                "last_seen": "now()"
            }
            # Upsert based on hostname (assuming hostname is unique per user in this simple model)
            # In a real scenario we'd use a unique UUID per device generated at pair time
            self.client.table("devices").upsert(data, on_conflict="hostname").execute()
        except Exception as e:
            logger.error(f"Cloud sync error (device): {e}")

    async def push_threat(self, device_hostname: str, threat_data: dict):
        """Push a new threat detection to cloud"""
        if not self.enabled: return

        try:
            # First get device ID
            res = self.client.table("devices").select("id").eq("hostname", device_hostname).execute()
            if not res.data:
                return
            
            device_id = res.data[0]['id']
            
            payload = {
                "device_id": device_id,
                "severity": threat_data.get('severity'),
                "type": threat_data.get('type'),
                "explanation": threat_data.get('explanation'),
                "file_path": threat_data.get('indicator'),
                "detected_at": "now()"
            }
            
            self.client.table("threats").insert(payload).execute()
            
            # Also create an alert
            alert_payload = {
                "device_id": device_id,
                "title": f"New {threat_data.get('severity')}/10 Threat Detected",
                "message": f"Found {threat_data.get('type')} on {device_hostname}",
            }
            self.client.table("alerts").insert(alert_payload).execute()
            
        except Exception as e:
            logger.error(f"Cloud sync error (threat): {e}")

# Global instance
cloud_sync = SupabaseSync()
