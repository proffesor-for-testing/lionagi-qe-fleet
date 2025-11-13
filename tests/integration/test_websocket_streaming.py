#!/usr/bin/env python3
"""
WebSocket streaming test for Phase 1 API integration.

Tests real-time job progress updates via WebSocket.
"""

import asyncio
import json
import sys
from typing import AsyncGenerator

import websockets
from websockets.client import WebSocketClientProtocol


async def test_websocket_job_streaming(job_id: str, api_key: str) -> None:
    """
    Test WebSocket streaming for a job.

    Args:
        job_id: Job ID to stream
        api_key: API key for authentication
    """
    ws_url = f"ws://localhost:8080/api/v1/job/{job_id}/stream"

    print(f"🔌 Connecting to WebSocket: {ws_url}")
    # Security: Mask API key in logs - show only first 8 chars
    print(f"🔑 Using API Key: {api_key[:8]}{'*' * 16}...\n")

    try:
        # Connect with authorization header
        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {api_key}"},
        ) as websocket:
            print("✅ WebSocket connected successfully!\n")

            # Receive and print messages
            message_count = 0
            async for message in websocket:
                message_count += 1
                data = json.loads(message)

                print(f"📨 Message {message_count}:")
                print(f"   Job ID: {data.get('job_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Progress: {data.get('progress')}%")
                print(f"   Updated: {data.get('updated_at')}")
                print()

                # Stop after receiving completion status
                if data.get("status") in ["completed", "failed", "cancelled"]:
                    print(f"✅ Job {data.get('status')}! Closing connection.\n")
                    break

            print(f"📊 Total messages received: {message_count}")
            return True

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def create_test_job(api_key: str) -> str:
    """
    Create a test job to stream.

    Args:
        api_key: API key for authentication

    Returns:
        Job ID
    """
    import aiohttp

    url = "http://localhost:8080/api/v1/test/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "target": "src/lionagi_qe/",
        "framework": "pytest",
        "test_type": "unit",
        "coverage_target": 85,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data["job_id"]
            else:
                raise Exception(f"Failed to create job: {response.status}")


async def main():
    """Main test execution."""
    print("=" * 60)
    print("WebSocket Streaming Integration Test")
    print("=" * 60)
    print()

    # Get API key from command line or use default
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        print("⚠️  No API key provided. Using placeholder.")
        print("   Usage: python test_websocket_streaming.py <api_key>")
        print()
        api_key = "aqe_placeholder"

    # Test 1: Create a job
    print("📝 Test 1: Creating test job...")
    try:
        job_id = await create_test_job(api_key)
        print(f"✅ Job created: {job_id}\n")
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        print("   Make sure the API server is running on port 8080")
        return False

    # Test 2: Stream job progress
    print("📝 Test 2: Streaming job progress via WebSocket...")
    success = await test_websocket_job_streaming(job_id, api_key)

    print("=" * 60)
    if success:
        print("✅ WebSocket streaming test PASSED")
    else:
        print("❌ WebSocket streaming test FAILED")
    print("=" * 60)

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
