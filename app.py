import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Analisis Butir Soal", page_icon="📝", layout="wide")
st.title("📝 Aplikasi Analisis Butir Soal")
st.write("Aplikasi ini digunakan untuk menghitung skor siswa, tingkat kesukaran, dan daya pembeda soal secara otomatis.")

# --- SIDEBAR: INPUT KUNCI JAWABAN ---
st.sidebar.header("1. Pengaturan Soal")
kunci_jawaban = st.sidebar.text_input("Masukkan Kunci Jawaban:", "ABBBBCCBCDACBAABBBBCBCBCCBBBCDCBCBBAACCC")
jumlah_soal = len(kunci_jawaban.replace("-", "").strip())
st.sidebar.info(f"Jumlah Soal terdeteksi: {jumlah_soal}")

# --- AREA UTAMA: UPLOAD DATA ---
st.header("2. Unggah Data Jawaban Siswa")
st.markdown("Unggah file Excel atau CSV yang memiliki minimal 2 kolom: **Nama** dan **Jawaban**.")
uploaded_file = st.file_uploader("Pilih file Excel/CSV", type=["xlsx", "csv"])

if uploaded_file is not None and jumlah_soal > 0:
    # Membaca file
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("File berhasil diunggah!")
        st.write("Pratinjau Data:", df.head())
        
        # Tombol Proses
        if st.button("🚀 Proses Analisis Sekarang"):
            with st.spinner("Sedang memproses data..."):
                
                # --- PROSES PENILAIAN ---
                matriks_skor = []
                for index, row in df.iterrows():
                    skor_siswa = []
                    jawab = str(row["Jawaban"]).strip()
                    
                    for i in range(jumlah_soal):
                        # Cek apakah jawaban benar (abaikan tanda strip jika siswa tidak menjawab)
                        if i < len(jawab) and jawab[i].upper() == kunci_jawaban[i].upper():
                            skor_siswa.append(1)
                        else:
                            skor_siswa.append(0)
                    matriks_skor.append(skor_siswa)
                
                # Membuat DataFrame Skor
                kolom_soal = [f"S_{i+1}" for i in range(jumlah_soal)]
                df_skor = pd.DataFrame(matriks_skor, columns=kolom_soal)
                df_hasil = pd.concat([df["Nama"], df_skor], axis=1)
                
                # Hitung Total
                df_hasil["Total_Benar"] = df_skor.sum(axis=1)
                df_hasil["Nilai"] = round((df_hasil["Total_Benar"] / jumlah_soal) * 100, 2)
                
                # --- ANALISIS BUTIR SOAL ---
                analisis = pd.DataFrame(index=kolom_soal)
                
                # 1. Tingkat Kesukaran (P)
                analisis["Tingkat_Kesukaran"] = df_skor.mean()
                def kat_kesukaran(p):
                    if p < 0.3: return "Sukar"
                    elif p <= 0.7: return "Sedang"
                    else: return "Mudah"
                analisis["Kategori_Kesukaran"] = analisis["Tingkat_Kesukaran"].apply(kat_kesukaran)
                
                # 2. Daya Pembeda (DP) - Menggunakan 50% Atas dan Bawah
                df_urut = df_hasil.sort_values(by="Total_Benar", ascending=False)
                n_kel = max(1, len(df_urut) // 2) # Minimal 1 agar tidak error jika data sedikit
                
                kel_atas = df_urut.iloc[:n_kel]
                kel_bawah = df_urut.iloc[-n_kel:]
                
                p_atas = kel_atas[kolom_soal].mean()
                p_bawah = kel_bawah[kolom_soal].mean()
                
                analisis["Daya_Pembeda"] = p_atas - p_bawah
                def kat_pembeda(dp):
                    if dp <= 0: return "Buruk/Ditolak"
                    elif dp <= 0.2: return "Jelek"
                    elif dp <= 0.4: return "Cukup"
                    elif dp <= 0.7: return "Baik"
                    else: return "Sangat Baik"
                analisis["Status_Soal"] = analisis["Daya_Pembeda"].apply(kat_pembeda)
                
                # --- TAMPILKAN HASIL ---
                st.header("3. Hasil Analisis")
                
                tab1, tab2 = st.tabs(["📊 Rekap Nilai Siswa", "📈 Analisis Butir Soal"])
                
                with tab1:
                    st.dataframe(df_hasil[["Nama", "Total_Benar", "Nilai"]], use_container_width=True)
                
                with tab2:
                    st.dataframe(analisis, use_container_width=True)
                
                # --- FITUR DOWNLOAD EXCEL ---
                st.markdown("---")
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_hasil.to_excel(writer, index=False, sheet_name='Nilai Siswa')
                    analisis.to_excel(writer, sheet_name='Analisis Soal')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Unduh Laporan Lengkap (Excel)",
                    data=excel_data,
                    file_name="Laporan_Analisis_Soal.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}. Pastikan format file sesuai.")
