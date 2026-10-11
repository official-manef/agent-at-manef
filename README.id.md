# Agent@Manef

**Satu sumber konteks. Banyak platform. Bisa dirapikan, dibackup, dan dipindahkan.**

[English README](README.md) · [Mulai](docs/getting-started.md) · [Migrasi](docs/migration.md) · [Backup](docs/backup-restore.md)

Agent@Manef adalah toolkit lokal untuk menyimpan identitas, mandat, konteks proyek, keputusan, dan prosedur agent secara terpusat. File untuk masing-masing platform dibuat dari sumber tersebut—bukan menjadi versi kebenaran yang berbeda.

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
git clone https://github.com/rahmanef63/agent-at-manef.git
cd agent-at-manef
python -m agent_at_manef init --target ../konteks-agent
python -m agent_at_manef init --target ../konteks-agent --apply
python -m agent_at_manef doctor --workspace ../konteks-agent
python -m agent_at_manef render --workspace ../konteks-agent --platform codex --target ../agent-codex --apply
python -m agent_at_manef verify --target ../agent-codex
```

Pada Windows, gunakan `py -3` bila diperlukan. Pada Linux/macOS, gunakan `python3` bila itulah nama interpreter yang tersedia. Perintah pertama hanya preview. `--apply` menulis hasil ke folder tujuan.

Workspace awal berisi contoh fiktif `researcher`. Ubah mandat dan konteksnya, atau tambahkan agent menggunakan perintah `new`. Buka folder agent hasil render di aplikasi tujuan dan ikuti panduan platformnya.

## Bukan hanya install

`inventory` memeriksa file instruksi yang dikenal tanpa membuka penyimpanan credential atau database sesi. `import` hanya mengambil file teks yang dipilih eksplisit dan menaruhnya sebagai kandidat di inbox; sumber lama tidak diubah.

Review kandidat, identitas pemilik, scope, konflik keputusan, tanggal informasi dan data privat. Baru perbarui charter/konteks canonical melalui review. Tidak ada promosi otomatis atau penggabungan akun hanya karena nama agent mirip.

`reconcile` menunjukkan file baru, berubah, konflik, dan usang. File yang diedit lokal tidak ditimpa. Opsi `--quarantine-stale --apply` hanya memindahkan output usang yang sebelumnya dikelola dan belum berubah ke `.ssot-history/`. Tidak ada penghapusan permanen otomatis.

## Backup dan pindah platform

```sh
python -m agent_at_manef backup --workspace ../konteks-agent --output ../backup-konteks.zip --apply
python -m agent_at_manef restore --archive ../backup-konteks.zip --target ../konteks-pulih --apply
python -m agent_at_manef render --workspace ../konteks-pulih --platform gemini --target ../agent-gemini --apply
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

`python -m agent_at_manef capabilities` menghasilkan kontrak versi, schema dan batas dukungan
berformat JSON, tanpa membaca akun atau workspace. MSO dapat menjadi consumer kontrak ini;
Agent@Manef tetap dapat digunakan tanpa MSO. Integrasi live MSO belum diverifikasi.

[Kontrak portabilitas](docs/portability.md) · [Integrasi MSO](docs/integrations/mso.md) ·
[Kepemilikan dan fork](docs/governance.md)

Upstream yang ditetapkan: **rahmanef63/agent-ssot**. Dibuat oleh
[Rahman](https://github.com/rahmanef63), dikelola bersama
[Manef](https://github.com/official-manef). Fork dipakai untuk kontribusi yang diperlukan,
bukan menggandakan sumber keputusan. Perubahan organisasi tidak dilakukan otomatis.

## Agent@Manef dan library

Nama produk kini **Agent@Manef**, slug repo `agent-at-manef`. Ini produk Manef yang dibuat Rahman;
upstream tetap ditujukan ke akun Rahman. Transfer kepemilikan masih menunggu penerimaan saat
pemeriksaan terakhir. Jangan menganggap pergantian nama sebagai transfer yang sudah selesai.

Namespace baru `agent_at_manef` dan CLI `agent-at-manef` tersedia melalui instalasi source.
Namespace/CLI lama dan format backup versi 1 dipertahankan. Belum ada publikasi PyPI/npm.
[API library](docs/library.md), [riset ekosistem](docs/research.md),
[pembagian file instruksi](docs/instruction-files.md), dan [rencana produk](docs/product.md).

Perintah `assess` membandingkan kebutuhan model, harness dan host dengan deklarasi target.
Kemampuan wajib yang hilang, belum diketahui, atau tanpa referensi bukti/tanggal tidak dianggap
terpenuhi. Hasilnya bukan izin eksekusi dan bukan bukti autentikasi atau keamanan VM.
Contoh di folder examples sengaja belum kompatibel; exit 2 adalah hasil yang diharapkan.

Kita mengambil pola yang berguna, bukan menyalin semua produk. Lisensi open-source,
source-available, model open-weight dan layanan hosted harus dibedakan. Integrasi manef.dev
dan library terdistribusi masih tahap berikutnya, bukan sudah live dari perubahan dokumentasi.

## Kandidat 0.2.0rc1

[Pemeriksaan rilis](docs/release.md) · [Kontrak adapter](docs/adapters.md) · [Metadata katalog](docs/catalog.md)

Adapter memakai satu registry yang direview. Katalog memvalidasi metadata lokal tanpa mengunduh
atau memasang agent. CI membangun wheel/sdist serta menguji instalasi offline dan pemulihan.
Ini artefak kandidat, bukan rilis registry, katalog hosted atau integrasi runtime live.

## Pemulihan terenkripsi opsional

ZIP konteks standar tetap tanpa enkripsi/signature. Modul opsional
[age/minisign](docs/secure-transfer.md) mengenkripsi ZIP yang tervalidasi dan memeriksa signature
pengirim tepercaya sebelum dekripsi serta restore v1. Signing tetap di terminal privat pengirim;
tidak ada key di repo. Program eksternal hanya berjalan dengan apply/execute eksplisit.
Pengujian kriptografi nyata terpisah dari core yang tidak memerlukan model atau harness.
