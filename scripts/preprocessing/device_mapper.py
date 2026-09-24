"""
Deterministic Device Mapper for TigerGraph Agentic Fraud Investigation.
Normalizes device attributes and constructs canonical DeviceProfile identifiers.
"""
import hashlib
from typing import Dict, Tuple

class DeviceMapper:
    @staticmethod
    def normalize_str(s: str) -> str:
        if not s:
            return ""
        return " ".join(s.strip().split())

    @classmethod
    def create_device_profile(
        cls,
        device_info: str,
        id_30_os: str,
        id_31_browser: str,
        id_33_screen: str,
        device_type: str = ""
    ) -> Tuple[str, str, Dict[str, str]]:
        """
        Returns:
            canonical_profile_str: Human-readable composite string (e.g. 'Windows | Windows 10 | chrome 63.0 | 1920x1080')
            device_id: Deterministic alphanumeric hash ID (e.g. 'DEV_a1b2c3d4e5f6')
            attributes: Dictionary of normalized components
        """
        dev = cls.normalize_str(device_info)
        os_val = cls.normalize_str(id_30_os)
        browser = cls.normalize_str(id_31_browser)
        screen = cls.normalize_str(id_33_screen)
        dtype = cls.normalize_str(device_type).lower()

        parts = [dev, os_val, browser, screen]
        if not any(parts):
            canonical_str = f"Unknown ({dtype if dtype else 'unknown'})"
        else:
            canonical_str = " | ".join(p if p else "Unknown" for p in parts)

        # Generate deterministic 12-char hex hash
        hash_digest = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()[:12]
        device_id = f"DEV_{hash_digest}"

        attributes = {
            "device_id": device_id,
            "device_info": dev,
            "os": os_val,
            "browser": browser,
            "screen": screen,
            "device_type": dtype,
            "canonical_profile_str": canonical_str
        }

        return canonical_str, device_id, attributes
