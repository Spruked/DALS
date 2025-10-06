"""
Command-line interface for the DALS Inventory Manager.
"""
import argparse
import asyncio
from .inventory_manager import UnitInventoryManager

def main():
    parser = argparse.ArgumentParser(description="DALS Inventory Manager CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List command
    list_parser = subparsers.add_parser("list", help="List all inventory records")
    list_parser.add_argument("--format", choices=["json", "table"], default="table", help="Output format")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific inventory record")
    get_parser.add_argument("asset_id", help="The asset ID of the record to retrieve")

    args = parser.parse_args()

    async def run():
        manager = UnitInventoryManager()
        await manager.initialize()

        if args.command == "list":
            records = await manager.get_all_records()
            if args.format == "json":
                import json
                print(json.dumps([r.to_dict() for r in records], indent=2))
            else:
                for record in records:
                    print(record)
        
        elif args.command == "get":
            record = await manager.get_latest_record(args.asset_id)
            if record:
                import json
                print(json.dumps(record.to_dict(), indent=2))
            else:
                print(f"No record found for asset ID: {args.asset_id}")

    asyncio.run(run())

if __name__ == "__main__":
    main()
