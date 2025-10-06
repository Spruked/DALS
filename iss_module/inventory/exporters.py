import csv
import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from ..models import UnitRecord

logger = logging.getLogger(__name__)

class DataExporter:
    """
    Data export manager for ISS Module
    
    Handles exporting data in various formats (JSON, CSV, Markdown)
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or self._get_default_output_dir()
        self.logger = logging.getLogger('ISS.DataExporter')
        self._ensure_output_dir()
    
    def _get_default_output_dir(self) -> str:
        """Get default output directory"""
        base_dir = Path(__file__).parent.parent
        output_dir = base_dir / 'data' / 'exports'
        return str(output_dir)
    
    def _ensure_output_dir(self):
        """Ensure output directory exists"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def export_log_entries_json(
        self,
        entries: List[UnitRecord],
        filename: Optional[str] = None,
        include_metadata: bool = True
    ) -> str:
        """
        Export log entries to JSON format
        
        Args:
            entries: List of UnitRecord objects to export
            filename: Output filename (auto-generated if None)
            include_metadata: Whether to include export metadata
        
        Returns:
            Path to the exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'inventory_export_{timestamp}.json'
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Prepare data
            export_data: Dict[str, Any] = {
                'entries': [entry.to_dict() for entry in entries]
            }
            
            if include_metadata:
                export_data['metadata'] = {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_entries': len(entries),
                    'exporter': 'DALS Data Exporter v2.0',
                    'format_version': '2.0'
                }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Exported {len(entries)} entries to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to export to JSON: {e}")
            raise
    
    async def export_log_entries_csv(
        self,
        entries: List[UnitRecord],
        filename: Optional[str] = None
    ) -> str:
        """
        Export log entries to CSV format
        
        Args:
            entries: List of UnitRecord objects to export
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to the exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'inventory_export_{timestamp}.csv'
            
            filepath = os.path.join(self.output_dir, filename)
            
            if not entries:
                # Create an empty file with headers if no entries
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(UnitRecord.get_field_names())
                return filepath

            # Get fieldnames from the dataclass
            fieldnames = UnitRecord.get_field_names()
            
            # Write CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for entry in entries:
                    writer.writerow(entry.to_dict())
            
            self.logger.info(f"Exported {len(entries)} entries to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            raise
    
    async def export_log_entries_markdown(
        self,
        entries: List[UnitRecord],
        filename: Optional[str] = None
    ) -> str:
        """
        Export log entries to Markdown format
        
        Args:
            entries: List of UnitRecord objects to export
            filename: Output filename (auto-generated if None)
        
        Returns:
            Path to the exported file
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'inventory_export_{timestamp}.md'
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Generate markdown content
            content_lines = []
            
            # Header
            content_lines.append("# DALS Inventory Export")
            content_lines.append("")
            content_lines.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            content_lines.append(f"**Total Units:** {len(entries)}")
            content_lines.append("")
            
            # Entries Table
            if entries:
                field_names = UnitRecord.get_field_names()
                content_lines.append(f"| {' | '.join(field_names)} |")
                content_lines.append(f"|{'|'.join(['---'] * len(field_names))}|")
                for entry in entries:
                    row_values = [str(v) for v in entry.to_dict().values()]
                    content_lines.append(f"| {' | '.join(row_values)} |")

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
            
            self.logger.info(f"Exported {len(entries)} entries to Markdown: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to export to Markdown: {e}")
            raise

# Convenient static class for easy usage
class Exporters:
    """
    Convenient static methods for data export
    
    Usage:
        from iss_module.inventory.exporters import Exporters
        Exporters.to_json(entries, "logs.json")
        Exporters.to_csv(entries, "logs.csv")
        Exporters.to_markdown(entries, "logs.md")
    """
    
    @staticmethod
    def to_json_sync(entries: List[Dict[str, Any]], filepath: str) -> str:
        """Export entries to JSON file (synchronous)"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': '2.0',
                    'exported_at': datetime.now().isoformat(),
                    'count': len(entries),
                    'entries': entries
                }, f, indent=2, ensure_ascii=False)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            raise
    
    @staticmethod
    def to_csv_sync(entries: List[Dict[str, Any]], filepath: str) -> str:
        """Export entries to CSV file (synchronous)"""
        try:
            if not entries:
                raise ValueError("No entries to export")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Get all possible fieldnames
            fieldnames = set()
            for entry in entries:
                fieldnames.update(entry.keys())
            fieldnames = sorted(list(fieldnames)) # Sort for consistent order
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(entries)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise
    
    @staticmethod
    def to_markdown_sync(entries: List[Dict[str, Any]], filepath: str) -> str:
        """Export entries to Markdown file (synchronous)"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# DALS Inventory Export\n\n")
                f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Total Entries:** {len(entries)}\n\n")

                if not entries:
                    f.write("No entries to display.\n")
                    return filepath

                headers = sorted(list(entries[0].keys()))
                f.write(f"| {' | '.join(headers)} |\n")
                f.write(f"|{'|'.join(['---'] * len(headers))}|\n")

                for entry in entries:
                    row_values = [str(entry.get(h, '')) for h in headers]
                    f.write(f"| {' | '.join(row_values)} |\n")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to export to Markdown: {e}")
            raise
    
    @staticmethod
    async def to_json(entries: List[UnitRecord], filepath: str, include_metadata: bool = True) -> str:
        """Export entries to JSON file"""
        exporter = DataExporter(output_dir=os.path.dirname(filepath))
        return await exporter.export_log_entries_json(
            entries, 
            filename=os.path.basename(filepath),
            include_metadata=include_metadata
        )
    
    @staticmethod
    async def to_csv(entries: List[UnitRecord], filepath: str) -> str:
        """Export entries to CSV file"""
        exporter = DataExporter(output_dir=os.path.dirname(filepath))
        return await exporter.export_log_entries_csv(
            entries,
            filename=os.path.basename(filepath)
        )
    
    @staticmethod
    async def to_markdown(entries: List[UnitRecord], filepath: str) -> str:
        """Export entries to Markdown file"""
        exporter = DataExporter(output_dir=os.path.dirname(filepath))
        return await exporter.export_log_entries_markdown(
            entries,
            filename=os.path.basename(filepath)
        )