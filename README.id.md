# Agent SSOT

**Satu sumber konteks. Banyak platform. Bisa dirapikan, dibackup, dan dipindahkan.**

[English README](README.md) · [Mulai](docs/getting-started.md) · [Migrasi](docs/migration.md) · [Backup](docs/backup-restore.md)

Agent SSOT adalah toolkit lokal untuk menyimpan identitas, mandat, konteks proyek, keputusan, dan prosedur agent secara terpusat. File untuk masing-masing platform dibuat dari sumber tersebut—bukan menjadi versi kebenaran yang berbeda.

Ini bukan server AI, layanan sinkronisasi otomatis, atau jaminan bahwa semua model akan berperilaku sama. Toolkit tidak memindahkan login, menyalin credential, menjalankan model, maupun membuat bot cloud otomatis.

## Tiga cara menggunakan

| Kebutuhan | Alur |
|---|---|
| Membuat agent baru | Buat workspace → definisikan mandat → isi konteks → render → verifikasi |
| Merapikan agent lama | Inventory → pilih file → import ke inbox → review → perbarui sumber canonical |
| Pindah mesin/platform | Backup konteks → restore ke folder baru → render platform lain → login privat → uji |

## Mulai dari source

Butuh Python 3.10+; tidak ada dependency runtime pihak ketiga.

```sh
git clone https://github.com/rahmanef63/agent-ssot.git
cd agent-ssot
python -m agent_ssot init --target ../konteks-agent
python -m agent_ssot init --target ../konteks-agent --apply
python -m agent_ssot doctor --workspace ../konteks-agent
python -m agent_ssot render --workspace ../konteks-agent --platform codex --target ../agent-codex --apply
python -m agent_ssot verify --target ../agent-codex
```

Pada Windows, gunakan `py -3` bila diperlukan. Pada Linux/macOS, gunakan `python3` bila itulah nama interpreter yang tersedia. Perintah pertama hanya preview. `--apply` menulis hasil ke folder tujuan.

Workspace awal berisi contoh fiktif `researcher`. Ubah mandat dan konteksnya, atau tambahkan agent menggunakan perintah `new`. Buka folder agent hasil render di aplikasi tujuan dan ikuti panduan platformnya.

## Bukan hanya install

`inventory` memeriksa file instruksi yang dikenal tanpa membuka penyimpanan credential atau database sesi. `import` hanya mengambil file teks yang dipilih eksplisit dan menaruhnya sebagai kandidat di inbox; sumber lama tidak diubah.

Review kandidat, identitas pemilik, scope, konflik keputusan, tanggal informasi dan data privat. Baru perbarui charter/konteks canonical melalui review. Tidak ada promosi otomatis atau penggabungan akun hanya karena nama agent mirip.

`reconcile` menunjukkan file baru, berubah, konflik, dan usang. File yang diedit lokal tidak ditimpa. Opsi `--quarantine-stale --apply` hanya memindahkan output usang yang sebelumnya dikelola dan belum berubah ke `.ssot-history/`. Tidak ada penghapusan permanen otomatis.

## Backup dan pindah platform

```sh
python -m agent_ssot backup --workspace ../konteks-agent --output ../backup-konteks.zip --apply
python -m agent_ssot restore --archive ../backup-konteks.zip --target ../konteks-pulih --apply
python -m agent_ssot render --workspace ../konteks-pulih --platform gemini --target ../agent-gemini --apply
```

Backup memuat konteks terkurasi dan checksum, bukan `.env`, cookie, database sesi atau inbox yang belum direview. ZIP belum dienkripsi dan belum ditandatangani. Simpan privat dan gunakan enkripsi yang disetujui untuk transfer.

## Dukungan platform

Generic, Codex, Claude, Gemini, Hermes, dan Grokbot memiliki output konteks/petunjuk setup. **Level dukungannya berbeda.** Hermes dan Grokbot pada toolkit publik ini berupa blueprint/paket pengaturan, bukan installer runtime atau importer bot live otomatis. Lihat [matriks kemampuan](docs/platforms.md).

## Yang perlu dijaga

Repo ini publik, tetapi konteks agent milikmu harus berada di workspace/repo privat terpisah. Template `env.example` hanya berisi nama variabel kosong. Credential asli disimpan di penyimpanan privat runtime/provider. Folder berbeda tidak otomatis menjadi sandbox.

Bedakan file disiapkan, konteks dibaca, pemahaman dibuktikan, akun terotorisasi, tugas berhasil, dan sesi berikutnya bisa melanjutkan. Semuanya membutuhkan bukti tersendiri.

[Arsitektur](docs/architecture.md) · [CLI](docs/cli.md) · [Keamanan](SECURITY.md) · [Kontribusi](CONTRIBUTING.md) · [Lisensi MIT](LICENSE)

## Independen dari model, harness, dan host

Format canonical tidak memilih model, provider, agent harness atau vendor VM. Core memakai
Python 3.10+ dan filesystem lokal. Model, tool, OAuth, proses dan state sesi diatur runtime.
Enam adapter adalah keluaran konteks/pengaturan, bukan enam runtime yang otomatis aktif.

`python -m agent_ssot capabilities` menghasilkan kontrak versi, schema dan batas dukungan
berformat JSON, tanpa membaca akun atau workspace. MSO dapat menjadi consumer kontrak ini;
Agent SSOT tetap dapat digunakan tanpa MSO. Integrasi live MSO belum diverifikasi.

[Kontrak portabilitas](docs/portability.md) · [Integrasi MSO](docs/integrations/mso.md) ·
[Kepemilikan dan fork](docs/governance.md)

Upstream yang ditetapkan: **rahmanef63/agent-ssot**. Dibuat oleh
[Rahman](https://github.com/rahmanef63), dikelola bersama
[Manef](https://github.com/official-manef). Fork dipakai untuk kontribusi yang diperlukan,
bukan menggandakan sumber keputusan. Perubahan organisasi tidak dilakukan otomatis.
