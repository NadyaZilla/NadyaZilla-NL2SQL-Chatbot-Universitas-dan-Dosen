DATABASE_SCHEMA = """
=== DATABASE SCHEMA ===

CREATE TABLE dosen (
  id_dosen INTEGER PRIMARY KEY AUTOINCREMENT,
  nidn TEXT NOT NULL UNIQUE,
  nama_lengkap TEXT NOT NULL,
  jenis_kelamin TEXT NOT NULL CHECK (jenis_kelamin IN ('L','P')),
  id_fakultas INTEGER NOT NULL,
  id_jabatan INTEGER NOT NULL,
  pendidikan_terakhir TEXT NOT NULL CHECK (pendidikan_terakhir IN ('S2','S3')),
  usia INTEGER NOT NULL CHECK (usia BETWEEN 25 AND 70),
  tanggal_bergabung DATE DEFAULT NULL,
  status_kepegawaian TEXT NOT NULL DEFAULT 'Tetap'
    CHECK (status_kepegawaian IN ('Tetap','Kontrak','DPK')),
  foto TEXT DEFAULT NULL,
  FOREIGN KEY (id_fakultas) REFERENCES fakultas (id_fakultas),
  FOREIGN KEY (id_jabatan) REFERENCES jabatan_fungsional (id_jabatan)
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE fakultas (
  id_fakultas INTEGER PRIMARY KEY AUTOINCREMENT,
  nama_fakultas VARCHAR(100) NOT NULL,
  kode_fakultas VARCHAR(10) NOT NULL UNIQUE,
  dekan VARCHAR(100) DEFAULT NULL,
  id_dekan INTEGER DEFAULT NULL,
  FOREIGN KEY (id_dekan) REFERENCES dosen (id_dosen)
);
CREATE TABLE jabatan_fungsional (
  id_jabatan INTEGER PRIMARY KEY AUTOINCREMENT,
  nama_jabatan VARCHAR(50) NOT NULL,
  kode_jabatan VARCHAR(10) NOT NULL UNIQUE,
  angka_kredit_min INTEGER DEFAULT NULL
);
CREATE TABLE remunerasi (
  id_remunerasi INTEGER PRIMARY KEY AUTOINCREMENT,
  id_dosen INTEGER NOT NULL,
  tahun INTEGER NOT NULL,
  bulan INTEGER NOT NULL CHECK (bulan BETWEEN 1 AND 12),
  gaji_pokok REAL NOT NULL,
  tunjangan_jabatan REAL DEFAULT 0.00,
  tunjangan_fungsional REAL DEFAULT 0.00,
  tunjangan_kinerja REAL DEFAULT 0.00,
  total_remunerasi REAL GENERATED ALWAYS AS (
    gaji_pokok + tunjangan_jabatan + tunjangan_fungsional + tunjangan_kinerja
  ) STORED,
  UNIQUE (id_dosen, tahun, bulan),
  FOREIGN KEY (id_dosen) REFERENCES dosen (id_dosen)
);
CREATE INDEX idx_dosen_fakultas ON dosen(id_fakultas);
CREATE INDEX idx_dosen_jabatan ON dosen(id_jabatan);
"""