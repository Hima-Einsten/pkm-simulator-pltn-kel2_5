#!/usr/bin/env python3
"""
Test struct packing untuk debugging
"""
import struct

print("="*60)
print("Testing struct.pack formats for ESP-E data")
print("="*60)

# Test data
p1, s1 = 155.0, 2
p2, s2 = 105.0, 2  
p3, s3 = 55.0, 2

# Test different formats
formats = [
    ('fBfBfB', 'Native alignment (default)'),
    ('<fBfBfB', 'Little-endian, standard sizes'),
    ('=fBfBfB', 'Native byte order, standard sizes'),
    ('@fBfBfB', 'Native byte order, native sizes (with padding)'),
]

for fmt, desc in formats:
    data = struct.pack(fmt, p1, s1, p2, s2, p3, s3)
    print(f"\nFormat: '{fmt}' - {desc}")
    print(f"  Size: {len(data)} bytes")
    print(f"  Hex: {' '.join([f'{b:02X}' for b in data])}")
    
    # With register byte
    full = [0x00] + list(data)
    print(f"  With register (0x00): {len(full)} bytes")
    print(f"  Full hex: {' '.join([f'{b:02X}' for b in full])}")

print("\n" + "="*60)
print("Expected: 15 bytes data + 1 register = 16 bytes total")
print("="*60)
