#!/usr/bin/env python3
"""
Test CoAP client to verify server is working
"""
import asyncio
import json
from aiocoap import Context, Message, Code

async def test_coap_post():
    """Send a test POST request to CoAP server"""
    
    # Test payload
    test_data = {
        "deviceId": "TEST_DEVICE",
        "timestamp": "2026-01-19T14:00:00Z",
        "data": {
            # "tilt_angle": 15.5,
            "accel_x": 0.1,
            "accel_y": 0.2,
            "accel_z": 9.8
        }
    }
    
    payload = json.dumps(test_data).encode('utf-8')
    
    # Create CoAP client
    context = await Context.create_client_context()
    
    # Test with different addresses
    test_urls = [
        "coap://127.0.0.1:5683/api/records/upload",
        "coap://10.0.2.15:5683/api/records/upload",
        "coap://0.0.0.0:5683/api/records/upload"
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print(f"Payload: {test_data}")
        print(f"{'='*60}")
        
        try:
            request = Message(code=Code.POST, payload=payload, uri=url)
            response = await context.request(request).response
            
            print(f"✓ Success!")
            print(f"  Response code: {response.code}")
            print(f"  Response payload: {response.payload.decode('utf-8')}")
            break
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    await context.shutdown()

if __name__ == "__main__":
    print("CoAP Server Test Client")
    print("Testing local CoAP server connection...")
    
    try:
        asyncio.run(test_coap_post())
    except KeyboardInterrupt:
        print("\nTest cancelled")
    except Exception as e:
        print(f"\nTest error: {e}")
