"""
YARA Rule Engine - Scan files with YARA rules
"""
import yara
import logging
from pathlib import Path
from typing import List, Dict
from config.settings import settings

logger = logging.getLogger(__name__)

class YaraEngine:
    """YARA-based malware detection engine"""
    
    def __init__(self, rules_dir: str = None):
        self.rules_dir = rules_dir or settings.yara_rules_dir
        self.compiled_rules = None
        self.load_rules()
    
    def load_rules(self):
        """Load and compile all YARA rules from rules directory"""
        rules_path = Path(self.rules_dir)
        
        if not rules_path.exists():
            logger.warning(f"YARA rules directory not found: {self.rules_dir}")
            rules_path.mkdir(parents=True, exist_ok=True)
            self._create_default_rules()
            return
        
        # Collect all .yar and .yara files
        rule_files = {}
        for rule_file in rules_path.glob('*.yar*'):
            namespace = rule_file.stem
            rule_files[namespace] = str(rule_file)
        
        if not rule_files:
            logger.warning("No YARA rules found, creating defaults")
            self._create_default_rules()
            return
        
        try:
            self.compiled_rules = yara.compile(filepaths=rule_files)
            logger.info(f"Loaded {len(rule_files)} YARA rule files")
        except Exception as e:
            logger.error(f"Error compiling YARA rules: {e}")
    
    def _create_default_rules(self):
        """Create default APT detection rules"""
        rules_path = Path(self.rules_dir)
        rules_path.mkdir(parents=True, exist_ok=True)
        
        # Default Cobalt Strike beacon rule
        cobalt_strike_rule = '''
rule CobaltStrike_Beacon {
    meta:
        description = "Detects Cobalt Strike Beacon payload"
        author = "APT Defender"
        severity = 10
    
    strings:
        $beacon1 = "beacon.dll" ascii
        $beacon2 = "ReflectiveLoader" ascii
        $ua = "Mozilla/5.0 (compatible; MSIE" ascii
        $pipe = "\\\\.\\\\pipe\\\\MSSE-" ascii wide
        $cmd = "IEX (New-Object Net.Webclient)" ascii
    
    condition:
        any of them
}
'''
        
        # Generic APT indicators
        apt_indicators_rule = '''
rule APT_Indicators {
    meta:
        description = "Generic APT behavior indicators"
        author = "APT Defender"
        severity = 8
    
    strings:
        $mimikatz1 = "sekurlsa::logonpasswords" ascii
        $mimikatz2 = "privilege::debug" ascii
        $powershell_download = "IEX (New-Object Net.WebClient).DownloadString" ascii
        $empire = "empire.py" ascii
        $metasploit = "meterpreter" ascii nocase
        $persistence1 = "HKCU\\\\Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run" ascii
        $reverse_shell = "bash -i >& /dev/tcp/" ascii
    
    condition:
        any of them
}
'''
        
        # Ransomware indicators
        ransomware_rule = '''
rule Ransomware_Indicators {
    meta:
        description = "Ransomware behavior patterns"
        author = "APT Defender"
        severity = 10
    
    strings:
        $encrypt1 = "AES" ascii wide
        $encrypt2 = "RSA" ascii wide
        $ransom_note = "bitcoin" nocase ascii wide
        $file_ext = ".locked" ascii wide
        $vssadmin = "vssadmin delete shadows" ascii
        $bcdedit = "bcdedit /set {default} recoveryenabled No" ascii
    
    condition:
        ($encrypt1 or $encrypt2) and ($ransom_note or $file_ext or $vssadmin or $bcdedit)
}
'''
        
        # Write default rules
        (rules_path / "cobalt_strike.yar").write_text(cobalt_strike_rule)
        (rules_path / "apt_indicators.yar").write_text(apt_indicators_rule)
        (rules_path / "ransomware.yar").write_text(ransomware_rule)
        
        logger.info("Created default YARA rules")
        
        # Reload
        self.load_rules()
    
    def scan_file(self, file_path: str) -> Dict:
        """
        Scan file with YARA rules
        
        Returns:
            {
                "matches": [...],
                "malicious": True/False,
                "explanation": "...",
                "severity": 1-10
            }
        """
        if not self.compiled_rules:
            return {"error": "No YARA rules loaded"}
        
        try:
            matches = self.compiled_rules.match(file_path)
            
            if not matches:
                return {
                    "matches": [],
                    "malicious": False
                }
            
            # Extract match details
            match_details = []
            max_severity = 0
            
            for match in matches:
                severity = int(match.meta.get('severity', 5))
                max_severity = max(max_severity, severity)
                
                match_details.append({
                    "rule": match.rule,
                    "description": match.meta.get('description', ''),
                    "severity": severity,
                    "tags": match.tags,
                    "strings": [str(s) for s in match.strings]
                })
            
            # Generate explanation
            rule_names = [m.rule for m in matches]
            explanation = f"File matched YARA rules: {', '.join(rule_names)}"
            
            return {
                "matches": match_details,
                "malicious": True,
                "explanation": explanation,
                "severity": max_severity
            }
        
        except Exception as e:
            logger.error(f"YARA scan error for {file_path}: {e}")
            return {"error": str(e)}
    
    def scan_process_memory(self, pid: int) -> Dict:
        """
        Scan running process memory (Linux only)
        Note: Requires root privileges
        """
        try:
            matches = self.compiled_rules.match(pid=pid)
            
            if not matches:
                return {"matches": [], "malicious": False}
            
            match_details = [
                {
                    "rule": m.rule,
                    "description": m.meta.get('description', ''),
                    "severity": int(m.meta.get('severity', 5))
                }
                for m in matches
            ]
            
            return {
                "matches": match_details,
                "malicious": True,
                "explanation": f"Process memory matched {len(matches)} YARA rules"
            }
        
        except Exception as e:
            logger.error(f"YARA process scan error for PID {pid}: {e}")
            return {"error": str(e)}
