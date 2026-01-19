#!/usr/bin/env python3
"""
Simple UDP listener test to verify network path
"""
import socket

def test_udp_bind():
    """Test if we can bind to UDP port 5683"""
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 5683))
        
        print("[SUCCESS] UDP port 5683 bound successfully!")
        print(f"Listening on: {sock.getsockname()}")
        print("\nWaiting for UDP packets... (Press Ctrl+C to stop)")
        print("=" * 60)
        
        while True:
            data, addr = sock.recvfrom(4096)
            print(f"\n[PACKET RECEIVED]")
            print(f"  From: {addr}")
            print(f"  Size: {len(data)} bytes")
            print(f"  Data: {data[:100]}")  # First 100 bytes
            print("=" * 60)
            
    except PermissionError as e:
        print(f"[ERROR] Permission denied: {e}")
        print("Need CAP_NET_BIND_SERVICE or run as root")
    except OSError as e:
        print(f"[ERROR] Cannot bind port: {e}")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        if sock:
            sock.close()
            print("Socket closed")

if __name__ == "__main__":
    test_udp_bind()
