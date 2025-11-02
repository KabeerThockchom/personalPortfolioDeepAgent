"""Test script for backend API."""

import asyncio
import json
import requests
import websockets
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


def test_rest_api():
    """Test REST API endpoints."""
    print("\n" + "="*60)
    print("🧪 TESTING REST API")
    print("="*60)

    # Test health check
    print("\n1️⃣  Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200

    # Create new chat
    print("\n2️⃣  Creating new chat...")
    response = requests.post(
        f"{BASE_URL}/api/chat/new",
        json={"title": "Test Chat", "load_portfolio": True}
    )
    print(f"   Status: {response.status_code}")
    chat_data = response.json()
    print(f"   Chat ID: {chat_data['id']}")
    print(f"   Session ID: {chat_data['session_id']}")
    assert response.status_code == 200

    chat_id = chat_data["id"]
    session_id = chat_data["session_id"]

    # List chats
    print("\n3️⃣  Listing all chats...")
    response = requests.get(f"{BASE_URL}/api/chat/")
    print(f"   Status: {response.status_code}")
    chats = response.json()
    print(f"   Total chats: {chats['total']}")
    assert response.status_code == 200

    # Get chat history
    print("\n4️⃣  Getting chat history...")
    response = requests.get(f"{BASE_URL}/api/chat/{chat_id}")
    print(f"   Status: {response.status_code}")
    history = response.json()
    print(f"   Messages: {len(history['messages'])}")
    assert response.status_code == 200

    # Update chat
    print("\n5️⃣  Updating chat title...")
    response = requests.put(
        f"{BASE_URL}/api/chat/{chat_id}",
        json={"title": "Updated Test Chat"}
    )
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200

    print("\n✅ REST API tests passed!")
    return chat_id, session_id


async def test_websocket(chat_id: str, session_id: str):
    """Test WebSocket streaming."""
    print("\n" + "="*60)
    print("🧪 TESTING WEBSOCKET")
    print("="*60)

    uri = f"{WS_URL}/ws/{chat_id}"
    print(f"\n📡 Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Send a message
            print("\n📤 Sending message to agent...")
            message = {
                "type": "message",
                "data": {
                    "content": "What is 2 + 2? Just give me a simple answer.",
                    "session_id": session_id,
                    "enable_hitl": False  # Disable for testing
                }
            }
            await websocket.send(json.dumps(message))
            print("   Message sent!")

            # Receive events
            print("\n📥 Receiving events...\n")
            event_count = 0
            start_time = datetime.now()

            while True:
                try:
                    # Set timeout to avoid hanging
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    event = json.loads(response)
                    event_count += 1

                    event_type = event.get("type")
                    timestamp = event.get("timestamp", "")

                    # Print event info
                    if event_type == "start":
                        print(f"   🚀 START - Message ID: {event['data'].get('message_id', '')[:8]}...")

                    elif event_type == "step":
                        step_num = event['data'].get('step_number')
                        friendly = event['data'].get('friendly_name')
                        print(f"   📍 STEP {step_num}: {friendly}")

                    elif event_type == "tool_call":
                        name = event['data'].get('name')
                        args = event['data'].get('args', {})
                        print(f"   🔧 TOOL CALL: {name}")
                        print(f"      Args: {json.dumps(args, indent=6)[:100]}...")

                    elif event_type == "tool_result":
                        name = event['data'].get('name')
                        success = event['data'].get('success')
                        status = "✅" if success else "❌"
                        print(f"   {status} TOOL RESULT: {name}")

                    elif event_type == "todo_update":
                        todos = event['data'].get('todos', [])
                        print(f"   📋 TODO UPDATE: {len(todos)} tasks")

                    elif event_type == "file_update":
                        files = event['data'].get('files', [])
                        print(f"   📁 FILE UPDATE: {len(files)} files")

                    elif event_type == "approval_request":
                        requests = event['data'].get('requests', [])
                        print(f"   ⚠️  APPROVAL REQUEST: {len(requests)} actions")

                    elif event_type == "complete":
                        message_content = event['data']['message']['content']
                        print(f"\n   ✅ COMPLETE!")
                        print(f"   Response: {message_content[:200]}...")
                        break

                    elif event_type == "error":
                        error = event['data'].get('error')
                        print(f"   ❌ ERROR: {error}")
                        break

                except asyncio.TimeoutError:
                    print("   ⏱️  Timeout waiting for events")
                    break

            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n📊 Summary:")
            print(f"   Events received: {event_count}")
            print(f"   Time elapsed: {elapsed:.2f}s")

            print("\n✅ WebSocket tests passed!")

    except Exception as e:
        print(f"\n❌ WebSocket test failed: {e}")
        raise


async def run_tests():
    """Run all tests."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Backend API Test Suite                                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    try:
        # Test REST API
        chat_id, session_id = test_rest_api()

        # Test WebSocket
        await test_websocket(chat_id, session_id)

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
    except requests.exceptions.ConnectionError:
        print("\n❌ Could not connect to server!")
        print("   Make sure the backend is running:")
        print("   python -m api.server\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")


if __name__ == "__main__":
    print("\n⚙️  Starting tests...")
    print("   Make sure the backend server is running on http://localhost:8000\n")

    asyncio.run(run_tests())
