"""
Inventory Management Module for DALS
Handles asset records, state changes, and data exporting.
"""

from .inventory_manager import UnitInventoryManager
from ..models import UnitRecord
from .exporters import DataExporter

__version__ = "2.0.0"
__all__ = [
    "UnitInventoryManager",
    "UnitRecord", 
    "DataExporter",
]