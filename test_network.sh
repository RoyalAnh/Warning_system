#!/bin/bash
# Network diagnostic script for CoAP UDP connectivity

echo "=== CoAP Server Network Diagnostics ==="
echo ""

echo "1. Checking if port 5683/UDP is listening:"
sudo netstat -ulnp | grep 5683 || sudo ss -ulnp | grep 5683
echo ""

echo "2. VM IP Address(es):"
ip addr show | grep "inet " | grep -v 127.0.0.1
echo ""

echo "3. Firewall status (ufw):"
sudo ufw status 2>/dev/null || echo "UFW not installed or not active"
echo ""

echo "4. Firewall status (iptables):"
sudo iptables -L -n | grep 5683 || echo "No iptables rules for 5683"
echo ""

echo "5. Testing UDP port with netcat (listening for 5 seconds):"
echo "Send a test packet to this IP on port 5683"
timeout 5 nc -u -l 5683 || echo "Timeout - no packet received"
echo ""

echo "6. Docker containers status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== Instructions ==="
echo "From your ESP32, send CoAP POST to: coap://<VM_IP>:5683/api/records/upload"
echo "Replace <VM_IP> with one of the addresses shown above"
echo ""
echo "VirtualBox settings needed:"
echo "- Network Adapter 1: Bridged Adapter (recommended)"
echo "  OR"
echo "- Network Adapter 1: NAT with Port Forwarding:"
echo "  Name: CoAP, Protocol: UDP, Host Port: 5683, Guest Port: 5683"
