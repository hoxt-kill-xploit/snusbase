"""
Standalone CLI for querying the Snusbase API.

Usage examples:
    python snusbase_cli.py search "email@example.com" --types email
    python snusbase_cli.py ipwhois 1.1.1.1 8.8.8.8
    python snusbase_cli.py stats
"""

import argparse
import os
import sys

# Optional dependency: python-dotenv. Fallback to a tiny loader if missing.
try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:
    def load_dotenv(path: str = ".env") -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                os.environ.setdefault(key, value)

from snusbase_client import SnusbaseAPI, format_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Snusbase API for leaked credentials and tools")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    search_parser = subparsers.add_parser("search", help="Search for leaked data")
    search_parser.add_argument("terms", nargs="+", help="Search terms")
    search_parser.add_argument("--types", nargs="+", required=True, help="Data types: email, username, lastip, password, hash, name, _domain")
    search_parser.add_argument("--wildcard", action="store_true", help="Enable wildcard search")
    search_parser.add_argument("--group-by", default="db", help="Group results by (db, false, or column name)")
    search_parser.add_argument("--tables", nargs="+", help="Limit to specific tables")

    subparsers.add_parser("stats", help="Get database statistics")

    ipwhois_parser = subparsers.add_parser("ipwhois", help="IP WHOIS lookup")
    ipwhois_parser.add_argument("ips", nargs="+", help="IP addresses to lookup")

    hash_parser = subparsers.add_parser("hash", help="Hash/password lookup")
    hash_parser.add_argument("terms", nargs="+", help="Hashes or passwords")
    hash_parser.add_argument("--types", nargs="+", required=True, help="Lookup types: hash, password")
    hash_parser.add_argument("--wildcard", action="store_true", help="Enable wildcard search")
    hash_parser.add_argument("--group-by", default="db", help="Group results by")
    hash_parser.add_argument("--tables", nargs="+", help="Limit to specific tables")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("SNUSBASE_API_KEY")
    if not api_key:
        print("Error: SNUSBASE_API_KEY environment variable not set.")
        print("Add it to your .env or export it before running this CLI.")
        sys.exit(1)

    api = SnusbaseAPI(api_key)

    if args.command == "search":
        print(f"Searching for: {', '.join(args.terms)} | types: {', '.join(args.types)}")
        results = api.search(args.terms, args.types, args.wildcard, args.group_by, args.tables)
        print(format_results(results))

    elif args.command == "stats":
        print("Fetching database statistics...")
        results = api.get_stats()
        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            features = results.get("features", {})
            print(f"Total Records: {results.get('rows', 'N/A'):,}")
            print(f"Available Databases: {len(results.get('tables', {}))}")
            print(f"Hash Lookup Databases: {len(features.get('hash_lookup', []))}")
            print(f"Combo Lookup Databases: {len(features.get('combo_lookup', []))}")
            print(f"Extended View Databases: {len(features.get('view_more', []))}")

    elif args.command == "ipwhois":
        print(f"Performing IP WHOIS for: {', '.join(args.ips)}")
        results = api.ip_whois(args.ips)
        print(format_results(results))

    elif args.command == "hash":
        print(f"Looking up: {', '.join(args.terms)} | types: {', '.join(args.types)}")
        results = api.hash_lookup(args.terms, args.types, args.wildcard, args.group_by, args.tables)
        print(format_results(results))


if __name__ == "__main__":
    main()
