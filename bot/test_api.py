#!/usr/bin/env python3
"""Debug script to check API responses."""

import asyncio
import sys
from pathlib import Path

# Add bot directory to path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from config import load_config
from services.api_client import APIClient


async def main():
    config = load_config()
    print(f"Using LMS_API_URL: {config.lms_api_url}")
    print(f"Using LMS_API_KEY: {config.lms_api_key[:10]}..." if config.lms_api_key else "LMS_API_KEY not set")
    print()
    
    client = APIClient(config.lms_api_url, config.lms_api_key)
    
    # Test /items/
    print("=== GET /items/ ===")
    try:
        items = await client._request("GET", "/items/")
        print(f"Got {len(items)} items")
        for item in items[:3]:
            print(f"  - {item}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test health
    print("=== Health check ===")
    try:
        result = await client.health_check()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test /labs
    print("=== GET /items/ (labs) ===")
    try:
        labs = await client.get_labs()
        print(f"Got {len(labs)} labs")
        for lab in labs:
            print(f"  - {lab}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test /analytics/pass-rates
    print("=== GET /analytics/pass-rates?lab=lab-04 ===")
    try:
        data = await client.get_pass_rates("lab-04")
        print(f"Response type: {type(data)}")
        print(f"Response: {data}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # Test /analytics/pass-rates for lab-01
    print("=== GET /analytics/pass-rates?lab=lab-01 ===")
    try:
        data = await client.get_pass_rates("lab-01")
        print(f"Response type: {type(data)}")
        print(f"Response: {data}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
