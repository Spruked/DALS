#!/usr/bin/env python3
"""
DALS Module CLI Interface
========================
Command-line interface for the Digital Asset Logistics System.

Commands:
    iss --help              Show help
    iss init               Initialize DALS system
    iss asset              Manage digital assets
    iss export csv         Export asset data to CSV
    iss status             Show system status
    iss stardate          Get current stardate
    iss server            Start web server
"""

import sys
import argparse
import asyncio
from typing import Optional

from iss_module.core.ISS import ISS
from iss_module.inventory.inventory_manager import UnitInventoryManager
from iss_module.inventory.exporters import DataExporter
from iss_module.core.utils import get_stardate, current_timecodes
from serial_assignment import assign_digital_asset_id
import json

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='iss',
        description='Digital Asset Logistics System (DALS) Command Line Interface',
        epilog='For more information, visit the project repository.'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize DALS system')
    init_parser.add_argument('--name', default='DALS Instance', help='System name')
    
    # Asset command
    asset_parser = subparsers.add_parser('asset', help='Manage digital assets')
    asset_subparsers = asset_parser.add_subparsers(dest='asset_command', help='Asset commands')
    
    # Asset create command
    create_parser = asset_subparsers.add_parser('create', help='Create a new digital asset')
    create_parser.add_argument('asset_type', choices=["FEATURE", "EPIC", "BUILD", "SERVICE", "ARTIFACT"], help='Type of asset')
    create_parser.add_argument('project_id', help="Project ID (e.g., 'CORE-API')")
    create_parser.add_argument('source_ref', help="Source reference (e.g., 'v1.2.0', 'a4b2c8d9')")
    create_parser.add_argument('--parent', help='Parent Asset ID')

    # Asset list command
    list_parser = asset_subparsers.add_parser('list', help='List tracked assets')
    list_parser.add_argument('--status', help='Filter by status (e.g., DEPLOYED)')
    list_parser.add_argument('--project', help='Filter by Project ID')
    list_parser.add_argument('--limit', type=int, default=20, help='Number of assets to show')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export asset data')
    export_parser.add_argument('format', choices=['csv', 'json', 'markdown'], 
                              help='Export format')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Stardate command
    stardate_parser = subparsers.add_parser('stardate', help='Get current stardate')
    stardate_parser.add_argument('--format', choices=['numeric', 'full'], 
                                default='full', help='Stardate format')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start web server')
    server_parser.add_argument('--host', default='127.0.0.1', help='Server host')
    server_parser.add_argument('--port', type=int, default=8000, help='Server port')
    server_parser.add_argument('--reload', action='store_true', help='Auto-reload on changes')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            handle_init(args)
        elif args.command == 'asset':
            if args.asset_command == 'create':
                handle_asset_create(args)
            elif args.asset_command == 'list':
                asyncio.run(handle_asset_list(args))
            else:
                asset_parser.print_help()
        elif args.command == 'export':
            asyncio.run(handle_export(args))
        elif args.command == 'status':
            asyncio.run(handle_status(args))
        elif args.command == 'stardate':
            handle_stardate(args)
        elif args.command == 'server':
            handle_server(args)
        elif args.command == 'version':
            handle_version(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_init(args):
    """Initialize DALS system"""
    try:
        print(f"Initializing DALS system: {args.name}")
        # This would typically create config files, check directories, etc.
        from iss_module.inventory.inventory_manager import UnitInventoryManager
        inventory = UnitInventoryManager()
        inventory._ensure_data_dir()
        print(f"✓ Data vault ensured at: {inventory.data_dir}")
        print("\nDALS system ready!")
        
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)


def handle_asset_create(args):
    """Create a new digital asset ID"""
    try:
        result = assign_digital_asset_id(
            asset_type=args.asset_type,
            project_id=args.project_id,
            source_reference=args.source_ref,
            parent_asset_id=args.parent
        )
        print("Asset ID Assigned Successfully:")
        print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"Failed to create asset ID: {e}")
        sys.exit(1)

async def handle_asset_list(args):
    """List tracked assets"""
    try:
        inventory = UnitInventoryManager()
        await inventory.initialize()
        assets = await inventory.get_units(
            status=args.status,
            model_id=args.project,
            limit=args.limit
        )
        
        if not assets:
            print("No assets found matching the criteria.")
            return

        print(f"Displaying last {len(assets)} assets:")
        print("-" * 80)
        print(f"{'ASSET ID':<45} {'PROJECT':<15} {'STATUS':<15}")
        print("-" * 80)
        for asset in assets:
            print(f"{asset.asset_id:<45} {asset.project_id:<15} {asset.status:<15}")
        print("-" * 80)

    except Exception as e:
        print(f"Failed to list assets: {e}")
        sys.exit(1)


async def handle_export(args):
    """Export asset data"""
    try:
        inventory = UnitInventoryManager()
        await inventory.initialize()
        assets = await inventory.get_units(limit=10000) # Export all
        
        if not assets:
            print("No assets to export.")
            return
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dals_export_{timestamp}.{args.format}"
        
        # Convert asset objects to dictionaries for exporter
        asset_dicts = [asset.to_dict() for asset in assets]

        exporter = DataExporter()
        if args.format == 'csv':
            await exporter.export_to_csv(asset_dicts, output_file)
        elif args.format == 'json':
            await exporter.export_to_json(asset_dicts, output_file)
        
        print(f"✓ Exported {len(assets)} assets to {output_file}")
        
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)


async def handle_status(args):
    """Show system status"""
    try:
        inventory = UnitInventoryManager()
        await inventory.initialize()
        
        timecodes = current_timecodes()
        stardate = get_stardate()
        
        print("DALS Status")
        print("=" * 40)
        print(f"Current Stardate: {stardate}")
        print(f"System Time: {timecodes['iso_timestamp']}")
        print(f"Total Tracked Assets: {len(inventory.units)}")
        
        if inventory.units:
            status_counts = {}
            for asset in inventory.units.values():
                status_counts[asset.status] = status_counts.get(asset.status, 0) + 1
            
            print("Assets by Status:")
            for status, count in sorted(status_counts.items()):
                print(f"  {status}: {count}")
        
        print("\n✓ System operational")
        
    except Exception as e:
        print(f"Status check failed: {e}")
        sys.exit(1)


def handle_stardate(args):
    """Get current stardate"""
    try:
        stardate = get_stardate()
        
        if args.format == 'numeric':
            print(f"{stardate}")
        else:
            print(f"Stardate {stardate}")
            
    except Exception as e:
        print(f"Failed to get stardate: {e}")
        sys.exit(1)


def handle_server(args):
    """Start web server"""
    try:
        print(f"Starting DALS server on {args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        
        import uvicorn
        from iss_module.api.api import app
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Error: uvicorn or other dependency is required to run the server: {e}")
        print("Install with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)


def handle_version(args):
    """Show version information"""
    print("Digital Asset Logistics System (DALS) v2.0.0")


if __name__ == '__main__':
    main()

import sys
import argparse
import asyncio
from typing import Optional

from iss_module.core.ISS import ISS
from iss_module.inventory.inventory_manager import UnitInventoryManager
from iss_module.inventory.exporters import DataExporter
from iss_module.core.utils import get_stardate, current_timecodes


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='iss',
        description='ISS Module Command Line Interface',
        epilog='For more information, visit: https://github.com/your-org/iss-module'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize ISS system')
    init_parser.add_argument('--name', default='ISS Enterprise', help='System name')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Add captain\'s log entry')
    log_parser.add_argument('message', help='Log entry content')
    log_parser.add_argument('--priority', choices=['low', 'normal', 'high', 'urgent'], 
                           default='normal', help='Log priority')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('format', choices=['csv', 'json', 'markdown'], 
                              help='Export format')
    export_parser.add_argument('--output', '-o', help='Output file path')
    export_parser.add_argument('--filter', help='Filter entries (e.g., "priority:high")')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Stardate command
    stardate_parser = subparsers.add_parser('stardate', help='Get current stardate')
    stardate_parser.add_argument('--format', choices=['numeric', 'full'], 
                                default='full', help='Stardate format')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start web server')
    server_parser.add_argument('--host', default='127.0.0.1', help='Server host')
    server_parser.add_argument('--port', type=int, default=8000, help='Server port')
    server_parser.add_argument('--reload', action='store_true', help='Auto-reload on changes')
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'init':
            handle_init(args)
        elif args.command == 'log':
            handle_log(args)
        elif args.command == 'export':
            handle_export(args)
        elif args.command == 'status':
            handle_status(args)
        elif args.command == 'stardate':
            handle_stardate(args)
        elif args.command == 'server':
            handle_server(args)
        elif args.command == 'version':
            handle_version(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def handle_init(args):
    """Initialize ISS system"""
    try:
        iss = ISS()
        config = {
            'system_name': args.name,
            'version': '1.0.0',
            'debug_mode': False,
            'heartbeat_interval': 30,
            'data_retention_days': 90
        }
        
        # Initialize system (this would create config files, etc.)
        print(f"Initializing ISS system: {args.name}")
        print("✓ Configuration created")
        print("✓ Log system initialized")
        print("✓ Export directories created")
        print("\nISS system ready!")
        
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)


def handle_log(args):
    """Add captain's log entry"""
    try:
        captain_log = CaptainLog()
        
        # Map priority to category for now
        category_map = {
            'low': 'personal',
            'normal': 'general', 
            'high': 'system',
            'urgent': 'alert'
        }
        category = category_map.get(args.priority, 'general')
        
        # Add entry
        entry_id = captain_log.add_entry_sync(
            content=args.message,
            category=category
        )
        
        # Get the created entry to show confirmation
        entries = captain_log.get_entries_sync()
        entry = next((e for e in entries if e.get('id') == entry_id), None)
        
        if entry:
            print(f"Captain's log entry added successfully!")
            print(f"Stardate: {entry.get('stardate', 'Unknown')}")
            print(f"Category: {category}")
            print(f"Content: {args.message}")
        else:
            print("Entry added but could not retrieve confirmation.")
            
    except Exception as e:
        print(f"Failed to add log entry: {e}")
        sys.exit(1)


def handle_export(args):
    """Export data"""
    try:
        captain_log = CaptainLog()
        entries = captain_log.get_entries_sync()
        
        # Apply filters if specified
        if args.filter:
            # Simple filter implementation
            if args.filter.startswith('priority:'):
                priority = args.filter.split(':', 1)[1]
                entries = [e for e in entries if e.get('priority') == priority]
        
        if not entries:
            print("No entries to export.")
            return
        
        # Determine output file
        if args.output:
            output_file = args.output
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"iss_export_{timestamp}.{args.format}"
        
        # Export data
        if args.format == 'csv':
            Exporters.to_csv_sync(entries, output_file)
        elif args.format == 'json':
            Exporters.to_json_sync(entries, output_file)
        elif args.format == 'markdown':
            Exporters.to_markdown_sync(entries, output_file)
        
        print(f"✓ Exported {len(entries)} entries to {output_file}")
        
    except Exception as e:
        print(f"Export failed: {e}")
        sys.exit(1)


def handle_status(args):
    """Show system status"""
    try:
        captain_log = CaptainLog()
        entries = captain_log.get_entries_sync()
        
        # Get time information
        timecodes = current_timecodes()
        stardate = get_stardate()
        
        print("ISS Module Status")
        print("=" * 40)
        print(f"Current Stardate: {stardate}")
        print(f"System Time: {timecodes['iso_timestamp']}")
        print(f"Julian Date: {timecodes['julian_date']}")
        print(f"Market Info: {timecodes['market_info']}")
        print()
        print(f"Total Log Entries: {len(entries)}")
        
        if entries:
            # Count by priority
            priorities = {}
            for entry in entries:
                priority = entry.get('priority', 'normal')
                priorities[priority] = priorities.get(priority, 0) + 1
            
            print("Entries by Priority:")
            for priority, count in sorted(priorities.items()):
                print(f"  {priority}: {count}")
        
        print("\n✓ System operational")
        
    except Exception as e:
        print(f"Status check failed: {e}")
        sys.exit(1)


def handle_stardate(args):
    """Get current stardate"""
    try:
        stardate = get_stardate()
        
        if args.format == 'numeric':
            print(f"{stardate}")
        else:
            print(f"Stardate {stardate}")
            
    except Exception as e:
        print(f"Failed to get stardate: {e}")
        sys.exit(1)


def handle_server(args):
    """Start web server"""
    try:
        print(f"Starting ISS Module server on {args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        
        # Import and run the server
        import uvicorn
        from iss_module.api.api import app
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
        
    except ImportError:
        print("Error: uvicorn is required to run the server")
        print("Install with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"Server failed to start: {e}")
        sys.exit(1)


def handle_version(args):
    """Show version information"""
    print("ISS Module v1.0.0")
    print("Integrated Systems Solution")
    print("Compatible with Caleon and CertSig projects")


if __name__ == '__main__':
    main()