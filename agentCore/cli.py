#!/usr/bin/env python3
"""
CLI interface for AgentCore library
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .utils.api2tool import api2tool, api2tool_file
from .providers.llm_providers import get_provider_info
from .logger.logger import get_logger

logger = get_logger("cli")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AgentCore - AI Agent Library with Tool Integration"
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert OpenAPI to tools')
    convert_parser.add_argument('source', help='OpenAPI JSON file path or URL')
    convert_parser.add_argument('-o', '--output', help='Output file path', default='generated_tools.py')
    convert_parser.add_argument('-b', '--base-url', help='Base URL for API calls')
    convert_parser.add_argument('-f', '--format',
                               choices=['tools', 'dict', 'file', 'names', 'info'],
                               default='file',
                               help='Output format')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show library and provider information')
    info_parser.add_argument('-p', '--provider', help='Specific provider to check')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate OpenAPI specification')
    validate_parser.add_argument('source', help='OpenAPI JSON file path or URL')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'convert':
            handle_convert(args)
        elif args.command == 'info':
            handle_info(args)
        elif args.command == 'version':
            handle_version()
        elif args.command == 'validate':
            handle_validate(args)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        logger.error(f"Command failed: {str(e)}")
        sys.exit(1)

def handle_convert(args):
    """Handle convert command"""
    logger.info(f"Converting OpenAPI from: {args.source}")

    if args.format == 'file':
        code = api2tool_file(args.source, args.output, args.base_url)
        logger.success(f"Generated tools file: {args.output}")
        print(f"✅ Tools file generated: {args.output}")
    else:
        result = api2tool(args.source, args.base_url, args.format)

        if args.format == 'info':
            print("📊 API Information:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        elif args.format == 'names':
            print("🔧 Available Tools:")
            for name in result:
                print(f"  - {name}")
        elif args.format in ['tools', 'dict']:
            print(f"✅ Generated {len(result)} tools")
            if args.format == 'tools':
                for tool in result[:3]:  # Show first 3
                    print(f"  - {tool['schema']['name']}: {tool['schema']['description']}")
                if len(result) > 3:
                    print(f"  ... and {len(result) - 3} more tools")
            else:  # dict
                for name in list(result.keys())[:3]:  # Show first 3
                    print(f"  - {name}")
                if len(result) > 3:
                    print(f"  ... and {len(result) - 3} more tools")

def handle_info(args):
    """Handle info command"""
    print("📋 AgentCore Library Information")
    print("=" * 40)

    # Library info
    from . import __version__
    print(f"Version: {__version__}")
    print()

    # Provider info
    if args.provider:
        try:
            provider_info = get_provider_info(args.provider)
            print(f"🔧 Provider: {args.provider}")
            for key, value in provider_info.items():
                if key != 'provider':
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"❌ Error getting provider info: {e}")
    else:
        try:
            # Default provider
            provider_info = get_provider_info()
            print(f"🔧 Current Provider: {provider_info['provider']}")
            for key, value in provider_info.items():
                if key != 'provider':
                    print(f"  {key}: {value}")
        except Exception as e:
            print(f"❌ Error getting provider info: {e}")

def handle_version():
    """Handle version command"""
    from . import __version__, __author__
    print(f"AgentCore v{__version__}")
    print(f"By {__author__}")

def handle_validate(args):
    """Handle validate command"""
    logger.info(f"Validating OpenAPI spec: {args.source}")

    try:
        result = api2tool(args.source, output_format="info")

        print("✅ OpenAPI specification is valid")
        print(f"  Title: {result.get('title', 'Unknown')}")
        print(f"  Version: {result.get('version', 'Unknown')}")
        print(f"  Tools count: {result.get('tool_count', 0)}")
        print(f"  Base URL: {result.get('base_url', 'Not specified')}")

        if result.get('tool_names'):
            print("  Available endpoints:")
            for name in result['tool_names'][:5]:  # Show first 5
                print(f"    - {name}")
            if len(result['tool_names']) > 5:
                print(f"    ... and {len(result['tool_names']) - 5} more")

    except Exception as e:
        print(f"❌ Invalid OpenAPI specification: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()