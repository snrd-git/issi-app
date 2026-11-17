# Skrining ISSI — aplikasi offline

Satu aplikasi untuk trading, investasi, dan pola naik besar saham syariah ISSI.
Tab: **Cari** (cek satu saham) · Trading · Investasi · Pola · Chart · Jurnal · Pengaturan.

## Isi folder

| File | Fungsi |
|---|---|
| `index.html` | Aplikasi |
| `data/` | Harga 4 tahun + fundamental (dibuat oleh `ambil_data.py`) |
| `ambil_data.py` | Mengunduh data dari Yahoo Finance |
| `issi_list.txt` | Daftar kode ISSI yang diikuti — perbarui tiap Mei & November |
| `sw.js`, `manifest.webmanifest`, `icon.svg` | Agar bisa dipasang di HP dan jalan offline |
| `.github/workflows/update.yml` | Pembaruan otomatis harian di GitHub |

## Cara 1 — di laptop saja (tanpa internet di aplikasi)

1. `python ambil_data.py` (setelah 16:15 WIB).
2. Buka `index.html` dengan dua kali klik.

## Cara 2 — di HP dengan pembaruan otomatis (GitHub Pages)

1. Buat akun GitHub, lalu repositori baru (mis. `issi-app`).
2. Unggah semua isi folder ini **kecuali** `data/`.
3. Repositori → Settings → Pages → Source: **GitHub Actions**.
4. Repositori → Actions → "Perbarui data ISSI" → **Run workflow** (pertama kali).
5. Buka alamat `https://<nama-akun>.github.io/issi-app/` di HP → menu browser → **Add to Home screen / Tambahkan ke layar utama**.

Setelah itu data diperbarui otomatis tiap hari bursa pukul 16:45 WIB. Saat HP online, aplikasi mengambil data terbaru ketika dibuka; saat offline, data terakhir tetap bisa dipakai.

## Catatan

- Jurnal, saham dimiliki, angka manual, dan pengaturan disimpan **di perangkat masing-masing** (tidak ikut ke GitHub). Pindahkan dengan menu Pengaturan → Cadangan.
- Repositori publik berarti kode, daftar saham, dan data harga dari Yahoo bisa dilihat orang lain. Tidak ada data pribadi di dalamnya.
- Yahoo kadang membatasi akses dari server GitHub; jika data gagal, jalankan ulang workflow atau jalankan `ambil_data.py` di laptop.
- Data fundamental Yahoo perlu dicek ulang dengan laporan keuangan resmi (idx.co.id).
