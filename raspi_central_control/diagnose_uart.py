#!/usr/bin/env python3
"""
Test ESP UART - Check if ESP can receive data
Langkah debugging sistematis
"""

import serial
import time

print("\n" + "="*70)
print("DIAGNOSA UART - ESP TIDAK MERESPONS")
print("="*70)

print("""
SITUASI:
- Port /dev/ttyAMA0 bisa dibuka ✅
- Kirim command, tidak ada respons ❌

KEMUNGKINAN PENYEBAB:
1. ESP tidak menerima data (RX wire masalah)
2. ESP menerima tapi tidak mengirim respons (TX wire masalah)
3. Wiring terbalik (TX→TX, RX→RX salah!)
4. ESP firmware belum diupload atau crash

LANGKAH TESTING:
""")

print("\n" + "="*70)
print("TEST 1: Cek apakah ESP mengirim data (TX)")
print("="*70)
print("Buka ESP Serial Monitor (USB) dulu")
print("Harusnya muncul: 'UART2 initialized'")
print()

input("Sudah buka ESP Serial Monitor? Press ENTER...")

print("\nMembuka /dev/ttyAMA0 dan mendengarkan...")

try:
    ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
    print("✅ Port opened")
    
    print("\nMendengarkan selama 10 detik...")
    print("Jika ESP-BC sudah upload firmware esp_uart_test_simple.ino,")
    print("akan muncul heartbeat setiap 5 detik")
    print("-" * 70)
    
    start = time.time()
    got_data = False
    
    while time.time() - start < 10:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"RX: {data}")
            got_data = True
        time.sleep(0.1)
    
    print("-" * 70)
    
    if got_data:
        print("\n✅ SUKSES! ESP bisa mengirim data (TX OK)")
        print("   Problem: ESP tidak menerima command (RX issue)")
        print()
        print("SOLUSI:")
        print("   1. Cek kabel RX: RasPi GPIO 14 (Pin 8) → ESP GPIO 16")
        print("   2. Pastikan CROSSED! (RasPi TX → ESP RX)")
        print("   3. Cek koneksi jumper wire (longgar?)")
        
    else:
        print("\n❌ TIDAK ADA DATA dari ESP!")
        print()
        print("KEMUNGKINAN:")
        print("   1. ESP firmware belum diupload")
        print("   2. ESP crash / restart loop")
        print("   3. TX wire tidak tersambung (ESP GPIO 17 → RasPi Pin 10)")
        print("   4. ESP Serial Monitor menunjukkan error?")
        print()
        print("CEK ESP Serial Monitor (USB):")
        print("   - Apakah muncul 'UART2 initialized'?")
        print("   - Apakah ada pesan error?")
        print("   - Apakah ESP restart berulang-ulang?")
    
    print("\n" + "="*70)
    print("TEST 2: Kirim data ke ESP dan cek Serial Monitor")
    print("="*70)
    print("Kita akan kirim command ke ESP.")
    print("CEK di ESP Serial Monitor (USB) apakah muncul 'RX ← ...'")
    print()
    
    input("Ready? Press ENTER...")
    
    # Clear buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    time.sleep(0.1)
    
    # Send test
    test_msg = '{"cmd":"ping"}\n'
    print(f"\nMengirim: {test_msg.strip()}")
    ser.write(test_msg.encode('utf-8'))
    ser.flush()
    print("✅ Data terkirim")
    
    print("\n🔍 CEK ESP SERIAL MONITOR (USB) SEKARANG!")
    print("   Harusnya muncul: RX ← {\"cmd\":\"ping\"}")
    print()
    
    print("Apakah muncul 'RX ← ...' di ESP Serial Monitor?")
    answer = input("(y/n): ").strip().lower()
    
    if answer == 'y':
        print("\n✅ ESP MENERIMA DATA!")
        print("   RX wire OK (RasPi TX → ESP RX)")
        print()
        print("   Masalahnya: ESP tidak mengirim respons")
        print()
        print("SOLUSI:")
        print("   1. Cek ESP code ada kirim respons?")
        print("   2. Cek TX wire: ESP GPIO 17 → RasPi GPIO 15 (Pin 10)")
        print("   3. Upload firmware: esp_uart_test_simple.ino")
        
        # Check response
        print("\nMenunggu respons dari ESP...")
        time.sleep(1)
        
        if ser.in_waiting > 0:
            resp = ser.readline().decode('utf-8', errors='replace').strip()
            print(f"RX: {resp}")
            print("\n✅ ADA RESPONS! Problem solved!")
        else:
            print("❌ Tidak ada respons")
            print("   TX wire issue (ESP → RasPi)")
    
    else:
        print("\n❌ ESP TIDAK MENERIMA DATA!")
        print()
        print("DIAGNOSA:")
        print("   RX wire tidak tersambung atau salah")
        print()
        print("CEK WIRING:")
        print("   ❌ SALAH: RasPi Pin 8 (TX) → ESP GPIO 17 (TX)")
        print("   ✅ BENAR: RasPi Pin 8 (TX) → ESP GPIO 16 (RX)")
        print()
        print("CEK FISIK:")
        print("   1. Kabel tersambung ke pin yang benar?")
        print("   2. Kabel tidak lepas/longgar?")
        print("   3. Jumper wire berfungsi? (test dengan multimeter)")
    
    ser.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY - CARA CEK WIRING")
print("="*70)
print("""
WIRING YANG BENAR:

Raspberry Pi                    ESP32
-----------                     -----
Pin 8  (GPIO 14, TX)  ───────→  GPIO 16 (RX2)  ← CROSSED!
Pin 10 (GPIO 15, RX)  ←───────  GPIO 17 (TX2)  ← CROSSED!
Pin 6  (GND)          ───────→  GND

CARA CEK:
1. RasPi Pin 8 (TX) HARUS ke ESP Pin yang RX (GPIO 16)
2. RasPi Pin 10 (RX) HARUS ke ESP Pin yang TX (GPIO 17)
3. GND harus tersambung

JIKA MASIH GAGAL:
1. Upload firmware: esp_uart_test_simple.ino
2. Jalankan lagi test ini
3. Foto wiring dan kirim
""")

print("\nSelesai!")
