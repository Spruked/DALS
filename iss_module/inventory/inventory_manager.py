"""
Inventory Manager for the Digital Asset Logistics System (DALS)
Manages records of digital assets, their status, and lifecycle history.
"""

import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import logging
from dataclasses import dataclass, field, asdict

from ..core.utils import get_stardate, format_timestamp
from ..core.validators import validate_log_entry, sanitize_input
from ..models import AssetDependency, UnitRecord

# --- Inventory Manager ---

class UnitInventoryManager:
    """
    Manages the inventory of all digital assets.
    This class handles the creation, updating, and retrieval of asset records.
    It uses an append-only JSON Lines file for persistent storage to ensure a robust audit trail.
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or self._get_default_data_dir()
        self.inventory_file = os.path.join(self.data_dir, 'dals_inventory.jsonl')
        self.units: Dict[str, UnitRecord] = {}  # In-memory cache for quick access
        self.logger = logging.getLogger('DALS.InventoryManager')
        self._ensure_data_dir()
        
    def _get_default_data_dir(self) -> str:
        """Get default data directory within the project structure."""
        base_dir = Path(__file__).parent.parent.parent # Moves up from iss_module/inventory to ISS_Module-main
        data_dir = base_dir / 'vault'
        return str(data_dir)
    
    def _ensure_data_dir(self):
        """Ensure the data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def initialize(self):
        """Initializes the inventory manager by loading records from the log."""
        try:
            await self.load_records()
            self.logger.info(f"Inventory Manager initialized with {len(self.units)} unique assets.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Inventory Manager: {e}", exc_info=True)
            raise
    
    async def load_records(self):
        """
        Loads and reconstructs the state of all assets from the JSONL log file.
        The log contains the entire history, so we process it to get the latest state for each asset.
        """
        self.units = {}
        if not os.path.exists(self.inventory_file):
            self.logger.warning("Inventory file not found. Starting with an empty inventory.")
            return

        try:
            with open(self.inventory_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    asset_id = record.get('asset_id')
                    if not asset_id:
                        continue
                    
                    # The log is a series of state snapshots. The last one for each ID wins.
                    # We can overwrite the entry in our in-memory dict.
                    # The AssetDependency needs to be re-hydrated into its dataclass
                    record['dependencies'] = [AssetDependency(**dep) for dep in record.get('dependencies', [])]
                    self.units[asset_id] = UnitRecord(**record)

            self.logger.info(f"Loaded {len(self.units)} asset records from {self.inventory_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from inventory file: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Failed to load asset records: {e}", exc_info=True)

    async def _append_to_log(self, record: UnitRecord):
        """Appends a new state record for an asset to the persistent log file."""
        try:
            record_dict = record.to_dict()
            with open(self.inventory_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record_dict) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to append to inventory log for asset {record.asset_id}: {e}", exc_info=True)
            raise

    async def create_unit_record(
        self,
        unit_serial: str,
        model_id: str,
        deployment_location: str,
        initial_audit_hash: str,
        source_unit_serial: Optional[str],
        audited_by: str
    ) -> UnitRecord:
        """Creates the very first record for a new digital asset."""
        # Input validation
        if not unit_serial or not isinstance(unit_serial, str):
            raise ValueError("Unit serial must be a non-empty string")
        if not model_id or not isinstance(model_id, str):
            raise ValueError("Model ID must be a non-empty string")
        if not deployment_location or not isinstance(deployment_location, str):
            raise ValueError("Deployment location must be a non-empty string")
        if not initial_audit_hash or not isinstance(initial_audit_hash, str):
            raise ValueError("Initial audit hash must be a non-empty string")
        if not audited_by or not isinstance(audited_by, str):
            raise ValueError("Audited by must be a non-empty string")
            
        if unit_serial in self.units:
            raise ValueError(f"Asset ID {unit_serial} already exists in the inventory.")

        now = format_timestamp()
        history_entry = {
            "timestamp": now,
            "status": "CREATED",
            "details": f"Asset record created by {audited_by}. Initial audit hash: {initial_audit_hash}.",
            "auditor": audited_by,
            "source_asset": source_unit_serial
        }

        record = UnitRecord(
            id=unit_serial,
            asset_id=unit_serial,
            project_id=model_id,
            status="PENDING",
            deployment_environment=deployment_location,
            history=[history_entry]
        )

        self.units[unit_serial] = record
        await self._append_to_log(record)
        self.logger.info(f"Created new asset record: {unit_serial}")
        return record

    async def get_unit_by_serial(self, unit_serial: str) -> Optional[UnitRecord]:
        """Retrieves a single asset record by its unique serial ID."""
        return self.units.get(unit_serial.upper())

    async def update_unit_status(
        self,
        unit_serial: str,
        new_status: str,
        update_details: Optional[str],
        components_update: Optional[List[AssetDependency]],
        audited_by: str
    ) -> Optional[UnitRecord]:
        """Updates the status and/or dependencies of an existing asset."""
        record = await self.get_unit_by_serial(unit_serial)
        if not record:
            return None

        record.status = new_status
        
        history_details = f"Status changed to {new_status} by {audited_by}."
        if update_details:
            history_details += f" Details: {update_details}"

        if components_update is not None:
            record.dependencies = components_update
            history_details += f" Dependencies updated: {[dep.dependency_name for dep in components_update]}."

        record.history.append({
            "timestamp": format_timestamp(),
            "status": new_status,
            "details": history_details,
            "auditor": audited_by
        })

        await self._append_to_log(record)
        self.logger.info(f"Updated asset {unit_serial} to status {new_status}")
        return record

    async def update_unit_components(
        self,
        unit_serial: str,
        new_status: str,
        location: Optional[str],
        components: List[AssetDependency],
        audited_by: str
    ) -> Optional[UnitRecord]:
        """Specifically handles deployment and component association."""
        record = await self.get_unit_by_serial(unit_serial)
        if not record:
            return None

        record.status = new_status
        if location:
            record.deployment_environment = location
        record.dependencies = components

        history_details = (
            f"Asset deployed to '{location}' with {len(components)} dependencies by {audited_by}."
        )
        
        record.history.append({
            "timestamp": format_timestamp(),
            "status": new_status,
            "details": history_details,
            "auditor": audited_by
        })

        await self._append_to_log(record)
        self.logger.info(f"Deployed asset {unit_serial} to {location}")
        return record

    async def get_units(
        self,
        status: Optional[str] = None,
        model_id: Optional[str] = None,
        limit: Optional[int] = 50
    ) -> List[UnitRecord]:
        """Retrieves a list of asset records with optional filtering."""        
        # Since we load all units into memory, filtering is straightforward.
        filtered_units = list(self.units.values())

        if status:
            filtered_units = [u for u in filtered_units if u.status.upper() == status.upper()]
        
        if model_id:
            filtered_units = [u for u in filtered_units if u.project_id.upper() == model_id.upper()]

        # Sort by timestamp (most recent first)
        filtered_units.sort(key=lambda x: x.timestamp, reverse=True)
        
        return filtered_units[:limit]


@dataclass
class LogEntry:
    """Data class for log entries"""
    id: str
    timestamp: str
    stardate: float
    content: str
    tags: List[str]
    category: str
    mood: Optional[str] = None
    location: Optional[str] = None
    attachments: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class CaptainLog:
    """
    Captain's Log management system
    
    Handles creation, storage, retrieval, and management of log entries
    
    Usage:
        log = CaptainLog(captain="Bryan", ship="Prometheus")
        log.add_entry("Engaged harmonizer module", category="System", location="Core")
    """
    
    def __init__(self, data_dir: Optional[str] = None, captain: Optional[str] = None, ship: Optional[str] = None):
        self.data_dir = data_dir or self._get_default_data_dir()
        self.log_file = os.path.join(self.data_dir, 'captain_log.json')
        self.entries: List[LogEntry] = []
        self.logger = logging.getLogger('ISS.CaptainLog')
        self.captain = captain or "Unknown"
        self.ship = ship or "ISS Module"
        self._ensure_data_dir()
        
    def _get_default_data_dir(self) -> str:
        """Get default data directory"""
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / 'data' / 'logs'
        return str(data_dir)
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize the captain's log system"""
        try:
            await self.load_entries()
            self.logger.info("Captain's Log system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Captain's Log: {e}")
            raise
    
    async def load_entries(self):
        """Load existing log entries from storage"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.entries = []
                for entry_data in data.get('entries', []):
                    entry = LogEntry(**entry_data)
                    self.entries.append(entry)
                
                self.logger.info(f"Loaded {len(self.entries)} log entries")
            else:
                self.entries = []
                self.logger.info("No existing log file found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to load log entries: {e}")
            self.entries = []
    
    async def save_entries(self):
        """Save log entries to storage"""
        try:
            data = {
                'version': '1.0',
                'created': format_timestamp(),
                'entries': [entry.to_dict() for entry in self.entries]
            }
            
            # Create backup first
            if os.path.exists(self.log_file):
                backup_file = f"{self.log_file}.backup"
                with open(self.log_file, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
            
            # Write new data
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug("Log entries saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save log entries: {e}")
            raise
    
    async def create_entry(
        self,
        content: str,
        category: str = 'personal',
        tags: Optional[List[str]] = None,
        mood: Optional[str] = None,
        location: Optional[str] = None
    ) -> LogEntry:
        """
        Create a new log entry
        
        Args:
            content: The log entry content
            category: Category of the entry (personal, mission, technical, etc.)
            tags: Optional tags for the entry
            mood: Optional mood indicator
            location: Optional location information
        
        Returns:
            Created LogEntry object
        """
        try:
            # Sanitize and validate input
            content = sanitize_input(content, max_length=10000)
            if not content:
                raise ValueError("Log entry content cannot be empty")
            
            # Generate entry
            now = datetime.now(timezone.utc)
            entry = LogEntry(
                id=self._generate_entry_id(),
                timestamp=now.isoformat(),
                stardate=get_stardate(),
                content=content,
                category=category,
                tags=tags or [],
                mood=mood,
                location=location,
                attachments=[]
            )
            
            # Validate entry
            entry_dict = entry.to_dict()
            if not validate_log_entry(entry_dict):
                raise ValueError("Invalid log entry data")
            
            # Add to collection
            self.entries.append(entry)
            
            # Save immediately
            await self.save_entries()
            
            self.logger.info(f"Created log entry {entry.id}")
            return entry
            
        except Exception as e:
            self.logger.error(f"Failed to create log entry: {e}")
            raise

    def _generate_entry_id(self) -> str:
        """Generate unique entry ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_entries_sync(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous version of get_entries for CLI usage
        
        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            limit: Maximum number of entries to return
        
        Returns:
            List of log entry dictionaries
        """
        try:
            # Load entries if not already loaded
            if not hasattr(self, 'entries') or not self.entries:
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    self.entries = []
                    for entry_data in data.get('entries', []):
                        entry = LogEntry(**entry_data)
                        self.entries.append(entry)
                else:
                    self.entries = []
            
            # Apply filters
            filtered_entries = []
            for entry in self.entries:
                # Convert to dict for filtering
                entry_dict = entry.dict() if hasattr(entry, 'dict') else entry.__dict__
                
                # Category filter
                if category and entry_dict.get('category') != category:
                    continue
                
                # Tags filter
                if tags:
                    entry_tags = entry_dict.get('tags', [])
                    if not any(tag in entry_tags for tag in tags):
                        continue
                
                # Date filters
                if start_date or end_date:
                    entry_time = datetime.fromisoformat(
                        entry_dict.get('timestamp', '').replace('Z', '+00:00')
                    )
                    if start_date and entry_time < start_date:
                        continue
                    if end_date and entry_time > end_date:
                        continue
                
                filtered_entries.append(entry_dict)
            
            # Apply limit
            if limit:
                filtered_entries = filtered_entries[-limit:]
            
            return filtered_entries
            
        except Exception as e:
            self.logger.error(f"Failed to get entries: {e}")
            return []

    async def get_entries(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[LogEntry]:
        """
        Retrieve log entries with optional filtering
        
        Args:
            category: Filter by category
            tags: Filter by tags (any match)
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            limit: Maximum number of entries to return
        
        Returns:
            List of matching LogEntry objects
        """
        filtered_entries = self.entries.copy()
        
        # Apply filters
        if category:
            filtered_entries = [e for e in filtered_entries if e.category == category]
        
        if tags:
            filtered_entries = [
                e for e in filtered_entries 
                if any(tag in e.tags for tag in tags)
            ]
        
        if start_date:
            filtered_entries = [
                e for e in filtered_entries
                if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) >= start_date
            ]
        
        if end_date:
            filtered_entries = [
                e for e in filtered_entries
                if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) <= end_date
            ]
        
        # Sort by timestamp (newest first)
        filtered_entries.sort(
            key=lambda x: datetime.fromisoformat(x.timestamp.replace('Z', '+00:00')),
            reverse=True
        )
        
        # Apply limit
        if limit:
            filtered_entries = filtered_entries[:limit]
        
        return filtered_entries
    
    async def get_entry_by_id(self, entry_id: str) -> Optional[LogEntry]:
        """Get a specific entry by ID"""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    async def update_entry(
        self,
        entry_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        mood: Optional[str] = None,
        location: Optional[str] = None
    ) -> bool:
        """
        Update an existing log entry
        
        Args:
            entry_id: ID of the entry to update
            content: New content (optional)
            tags: New tags (optional)
            mood: New mood (optional)
            location: New location (optional)
        
        Returns:
            True if entry was updated successfully
        """
        try:
            entry = await self.get_entry_by_id(entry_id)
            if not entry:
                return False
            
            # Update fields
            if content is not None:
                entry.content = sanitize_input(content, max_length=10000)
            if tags is not None:
                entry.tags = tags
            if mood is not None:
                entry.mood = mood
            if location is not None:
                entry.location = location
            
            # Save changes
            await self.save_entries()
            
            self.logger.info(f"Updated log entry {entry_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update entry {entry_id}: {e}")
            return False
    
    async def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a log entry
        
        Args:
            entry_id: ID of the entry to delete
        
        Returns:
            True if entry was deleted successfully
        """
        try:
            for i, entry in enumerate(self.entries):
                if entry.id == entry_id:
                    del self.entries[i]
                    await self.save_entries()
                    self.logger.info(f"Deleted log entry {entry_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete entry {entry_id}: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the log entries"""
        total_entries = len(self.entries)
        
        if total_entries == 0:
            return {
                'total_entries': 0,
                'categories': {},
                'tags': {},
                'date_range': None
            }
        
        # Category breakdown
        categories = {}
        for entry in self.entries:
            categories[entry.category] = categories.get(entry.category, 0) + 1
        
        # Tag breakdown
        tags = {}
        for entry in self.entries:
            for tag in entry.tags:
                tags[tag] = tags.get(tag, 0) + 1
        
        # Date range
        timestamps = [
            datetime.fromisoformat(e.timestamp.replace('Z', '+00:00'))
            for e in self.entries
        ]
        date_range = {
            'earliest': min(timestamps).isoformat(),
            'latest': max(timestamps).isoformat()
        }
        
        return {
            'total_entries': total_entries,
            'categories': categories,
            'tags': dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)),
            'date_range': date_range
        }
    
    async def search_entries(self, query: str) -> List[LogEntry]:
        """
        Search log entries by content
        
        Args:
            query: Search query string
        
        Returns:
            List of matching LogEntry objects
        """
        query_lower = query.lower()
        matching_entries = []
        
        for entry in self.entries:
            if (query_lower in entry.content.lower() or
                query_lower in entry.category.lower() or
                any(query_lower in tag.lower() for tag in entry.tags)):
                matching_entries.append(entry)
        
        # Sort by relevance (exact matches first)
        matching_entries.sort(
            key=lambda x: x.content.lower().count(query_lower),
            reverse=True
        )
        
        return matching_entries