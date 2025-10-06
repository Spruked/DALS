# core/ISS.py
import logging
from .utils import (
    get_stardate,
    current_timecodes,
    ensure_folder,
)
from ..inventory.exporters import DataExporter as Exporters
from ..inventory.inventory_manager import CaptainLog


class ISS:
    """
    Interplanetary Stardate Synchrometer (ISS)
    -----------------------------------------
    Core orchestrator for time anchoring, captain's logs, 
    and module management. Designed for plug-and-play use 
    with Caleon and CertSig systems.
    """

    def __init__(self, system_name: str = "ISS"):
        self.system_name = system_name
        self.status = "healthy"
        self.modules = {}        # dynamically loaded modules
        self.logs = []           # local storage for logs
        self.log_folder = ensure_folder("logs")
        self.captain_log = CaptainLog()
        logging.basicConfig(level=logging.INFO)

    # ----------------------
    # Health / Heartbeat
    # ----------------------
    def heartbeat(self) -> bool:
        """
        Check system health and all loaded modules.
        """
        healthy = self.status == "healthy"
        for name, module in self.modules.items():
            hb = getattr(module, "heartbeat", None)
            if callable(hb):
                if not hb():
                    logging.warning(f"⚠️ Module {name} unhealthy")
                    healthy = False
        return healthy

    async def shutdown(self):
        """
        Gracefully shutdown the ISS system and all modules.
        """
        logging.info(f"Shutting down {self.system_name}...")
        
        # Shutdown all modules
        for name, module in self.modules.items():
            shutdown_method = getattr(module, "shutdown", None)
            if callable(shutdown_method):
                try:
                    # Check if the shutdown method is async
                    import asyncio
                    if asyncio.iscoroutinefunction(shutdown_method):
                        await shutdown_method()
                    else:
                        shutdown_method()
                    logging.info(f"Module {name} shutdown complete")
                except Exception as e:
                    logging.error(f"Error shutting down module {name}: {e}")
        
        self.status = "shutdown"
        logging.info(f"{self.system_name} shutdown complete")

    def get_status(self) -> dict:
        """
        Get comprehensive ISS system status
        """
        from .utils import current_timecodes
        
        timecodes = current_timecodes()
        
        return {
            "system_name": self.system_name,
            "status": self.status,
            "modules_loaded": len(self.modules),
            "module_list": list(self.modules.keys()),
            "current_stardate": timecodes["stardate"],
            "current_julian": timecodes["julian_date"],
            "iso_timestamp": timecodes["iso_timestamp"],
            "unix_timestamp": timecodes["unix_timestamp"],
            "heartbeat_healthy": self.heartbeat(),
            "log_entries": len(self.logs),
            "time_anchor_hash": timecodes["anchor_hash"]
        }
