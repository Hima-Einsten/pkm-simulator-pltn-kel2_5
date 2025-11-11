# Simulator PLTN v1.0 (Pembangkit Listrik Tenaga Nuklir)

Dokumentasi ini menjelaskan arsitektur, fungsi, dan alur kerja dari proyek simulasi PLTN yang dibangun menggunakan beberapa mikrokontroler ESP32.

## Gambaran Umum

Proyek ini adalah simulator **Pembangkit Listrik Tenaga Nuklir tipe PWR (Pressurized Water Reactor)** yang terdistribusi. Setiap modul ESP32 merepresentasikan komponen atau subsistem yang berbeda dari sebuah PLTN, dan mereka berkomunikasi satu sama lain untuk menciptakan simulasi proses yang saling bergantung, mulai dari kontrol reaktor hingga pembangkitan listrik.

## Arsitektur Sistem & Alur Komunikasi

Sistem ini menggunakan komunikasi serial (UART) berantai untuk mengalirkan data dari satu modul ke modul lainnya.

```
                               +-> [ESP-E: Visualizer Aliran Primer]
                               |
                               +-> [ESP-F: Visualizer Aliran Sekunder]
[ESP-A: Panel Kontrol Utama] --+
(Broadcast Status Sistem)      |
                               +-> [ESP-G: Visualizer Aliran Tersier]
                               |
                               +-> [ESP-B: Inti Reaktor & Batang Kendali] --(Data Posisi Batang)--> [ESP-C: Turbin & Generator]
```

1.  **ESP-A** bertindak sebagai **Master** yang menyiarkan (broadcast) status sistem (tekanan & status pompa) ke semua modul lain.
2.  **ESP-E, F, dan G** mendengarkan siaran dari ESP-A dan bertindak secara independen sebagai visualizer.
3.  **ESP-B** mendengarkan siaran dari ESP-A untuk logika pengaman (*interlock*), kemudian mengirimkan datanya sendiri (posisi batang kendali) secara spesifik ke **ESP-C**.
4.  **ESP-C** menerima data dari ESP-B untuk mensimulasikan pembangkitan listrik.

---

## Rincian Fungsi per Modul

### 1. `ESP_A_Rev_1` (Panel Kontrol Utama)

-   **Folder:** `ESP_A_Rev_1/`
-   **Fungsi Utama:** Antarmuka utama bagi operator untuk mengontrol dan memonitor kondisi dasar reaktor.
-   **Input:** 8 tombol untuk mengatur tekanan *pressurizer* dan menyalakan/mematikan 3 pompa sirkuit pendingin.
-   **Output:**
    -   4x Layar OLED untuk menampilkan status tekanan dan pompa.
    -   Buzzer sebagai alarm peringatan tekanan tinggi.
    -   Sinyal PWM untuk menggerakkan motor fisik pompa.
-   **Komunikasi:** Menyebarkan (broadcast) data `{tekanan, status_pompa1, status_pompa2, status_pompa3}` ke semua ESP lain melalui UART.

### 2. `ESP_B_Rev_1` (Inti Reaktor & Batang Kendali)

-   **Folder:** `ESP_B_Rev_1/`
-   **Fungsi Utama:** Mensimulasikan inti reaktor, kontrol daya melalui batang kendali, dan logika keamanan utama.
-   **Input:**
    -   Menerima data status dari ESP-A.
    -   Tombol-tombol lokal untuk menggerakkan 3 batang kendali (servo).
    -   Tombol darurat (SCRAM) untuk menurunkan semua batang kendali.
-   **Output:**
    -   Menggerakkan motor servo yang merepresentasikan batang kendali.
    -   Menampilkan posisi batang dan daya termal (`kwThermal`) yang dihasilkan di 4x OLED.
-   **Logika Kunci:** Batang kendali **hanya bisa dioperasikan** jika semua pompa aktif dan tekanan sistem sudah mencukupi (fitur *interlock*).
-   **Komunikasi:** Mengirim data `{posisi_batang1, posisi_batang2, posisi_batang3}` ke ESP-C.

### 3. `esp_c` (Sistem Pembangkit Listrik)

-   **Folder:** `esp_c/`
-   **Fungsi Utama:** Mensimulasikan proses konversi energi panas menjadi energi listrik (siklus sekunder).
-   **Input:** Menerima data posisi batang kendali dari ESP-B.
-   **Output:** Mengontrol relay dan kecepatan motor/kipas untuk komponen seperti:
    -   Generator Uap (*Steam Generator*)
    -   Turbin
    -   Kondensor
    -   Menara Pendingin (*Cooling Tower*)
-   **Logika Kunci:** Menggunakan *State Machine* (IDLE, STARTING_UP, RUNNING, SHUTTING_DOWN) berdasarkan level daya yang diterima dari ESP-B untuk menjalankan sekuens operasi secara bertahap.
-   **Komunikasi:** Mengirim data "Level Daya" final ke modul selanjutnya (ESP-D, jika ada).

### 4. `ESP_E`, `ESP_F`, `ESP_G` (Visualizer Aliran Pendingin)

-   **Folder:** `ESP_E_Aliran_Primer/`, `ESP_F_Aliran_Sekunder/`, `ESP_G_Aliran_Tersier/`
-   **Fungsi Utama:** Memberikan representasi visual dari aliran fluida di tiga sirkuit pendingin yang berbeda.
    -   `ESP-E`: Sirkuit Primer (dari reaktor).
    -   `ESP-F`: Sirkuit Sekunder (uap ke turbin).
    -   `ESP-G`: Sirkuit Tersier (pendinginan kondensor).
-   **Input:** Menerima data broadcast dari ESP-A.
-   **Output:** Animasi "aliran" menggunakan 16 LED. Kecepatan animasi disesuaikan dengan status pompa yang relevan (`OFF`, `STARTING`, `ON`, `SHUTTING_DOWN`).

---

## Alur Kerja Simulasi (Cara Menggunakan)

1.  **Inisialisasi:** Nyalakan semua sistem ESP.
2.  **Kontrol Awal (di ESP-A):**
    -   Gunakan tombol di **ESP-A** untuk menaikkan tekanan *pressurizer* hingga mencapai level operasi normal (misal: 150 bar).
    -   Nyalakan Pompa Primer, Sekunder, dan Tersier secara berurutan menggunakan tombol di **ESP-A**.
3.  **Visualisasi Aliran (di ESP-E, F, G):**
    -   Amati modul **ESP-E, F, dan G**. Animasi LED akan mulai bergerak, menandakan bahwa sirkuit pendingin sudah aktif.
4.  **Aktivasi Reaktor (di ESP-B):**
    -   Pindah ke **ESP-B**. Sistem sekarang sudah tidak terkunci (*interlock* terbuka).
    -   Gunakan tombol di **ESP-B** untuk mulai menaikkan (menarik keluar) batang kendali secara perlahan.
    -   Amati nilai `kwThermal` di layar OLED ESP-B yang mulai meningkat.
5.  **Pembangkitan Listrik (di ESP-C):**
    -   Amati modul **ESP-C**. Setelah batang kendali di ESP-B mencapai posisi tertentu, ESP-C akan memulai sekuens startup secara otomatis. Anda akan melihat motor dan kipas mulai berputar secara bertahap.
6.  **Shutdown Normal:**
    -   Turunkan kembali semua batang kendali di **ESP-B** ke posisi 0%.
    -   Modul **ESP-C** akan memulai sekuens shutdown.
    -   Matikan ketiga pompa melalui **ESP-A**.
7.  **Shutdown Darurat:**
    -   Tekan tombol **Emergency** di **ESP-B**. Semua batang kendali akan langsung turun ke 0%, dan sistem pembangkitan di ESP-C akan mati.
