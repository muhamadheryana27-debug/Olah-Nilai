import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Analisis Butir Soal", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS UNTUK UI LEBIH CLEAN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card style untuk Metric */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.03);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HEADER DASHBOARD ---
st.title("🎯 Dashboard Analisis Butir Soal")
st.markdown("Dapatkan *insight* mendalam dari hasil evaluasi siswa secara instan dan akurat.")
st.divider()

# --- 4. PENGATURAN DI SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    # MENGGUNAKAN TEXT_INPUT AGAR CUKUP TEKAN ENTER DI HP
    kunci_jawaban = st.text_input("Kunci Jawaban:", "ABBBBCCBCDACBAABBBBCBCBCCBBBCDCBCBBAACCC")
    jumlah_soal = len(kunci_jawaban.replace("-", "").strip())
    st.info(f"📌 **Jumlah Soal:** {jumlah_soal} butir")
    
    st.markdown("---")
    st.header("📂 Unggah Data")
    uploaded_file = st.file_uploader("Format didukung: Excel / CSV", type=["xlsx", "csv"])

# --- 5. LOGIKA UTAMA ---
if uploaded_file is not None and jumlah_soal > 0:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        with st.expander("👀 Lihat Pratinjau Data Mentah"):
            st.dataframe(df.head(), use_container_width=True)
            
        with st.spinner("Menganalisis jawaban siswa..."):
            
            # -- Proses Skoring --
            matriks_skor = []
            for index, row in df.iterrows():
                skor_siswa = []
                jawab = str(row["Jawaban"]).strip()
                
                for i in range(jumlah_soal):
                    if i < len(jawab) and jawab[i].upper() == kunci_jawaban[i].upper():
                        skor_siswa.append(1)
                    else:
                        skor_siswa.append(0)
                matriks_skor.append(skor_siswa)
            
            kolom_soal = [f"S_{i+1}" for i in range(jumlah_soal)]
            df_skor = pd.DataFrame(matriks_skor, columns=kolom_soal)
            df_hasil = pd.concat([df["Nama"], df_skor], axis=1)
            
            df_hasil["Total_Benar"] = df_skor.sum(axis=1)
            df_hasil["Nilai"] = round((df_hasil["Total_Benar"] / jumlah_soal) * 100, 2)
            
            # -- Analisis Butir Soal --
            analisis = pd.DataFrame(index=kolom_soal)
            analisis["Tingkat_Kesukaran"] = round(df_skor.mean(), 2)
            
            def kat_kesukaran(p):
                if p < 0.3: return "Sukar 🔴"
                elif p <= 0.7: return "Sedang 🟡"
                else: return "Mudah 🟢"
            analisis["Kategori_Kesukaran"] = analisis["Tingkat_Kesukaran"].apply(kat_kesukaran)
            
            df_urut = df_hasil.sort_values(by="Total_Benar", ascending=False)
            n_kel = max(1, len(df_urut) // 2)
            
            p_atas = df_urut.iloc[:n_kel][kolom_soal].mean()
            p_bawah = df_urut.iloc[-n_kel:][kolom_soal].mean()
            
            analisis["Daya_Pembeda"] = round(p_atas - p_bawah, 2)
            def kat_pembeda(dp):
                if dp <= 0: return "Buruk ❌"
                elif dp <= 0.2: return "Jelek ⚠️"
                elif dp <= 0.4: return "Cukup 🆗"
                elif dp <= 0.7: return "Baik 👍"
                else: return "Sangat Baik 🌟"
            analisis["Status_Soal"] = analisis["Daya_Pembeda"].apply(kat_pembeda)

        # --- 6. TAMPILAN DASHBOARD METRICS ---
        st.subheader("📊 Ringkasan Kelas")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Siswa", f"{len(df)} Orang")
        col2.metric("Rata-rata Nilai", f"{round(df_hasil['Nilai'].mean(), 1)}")
        col3.metric("Nilai Tertinggi", f"{df_hasil['Nilai'].max()}")
        col4.metric("Nilai Terendah", f"{df_hasil['Nilai'].min()}")
        
        st.divider()
        
        # --- 7. TAMPILAN TAB INTERAKTIF ---
        tab1, tab2, tab3 = st.tabs(["📊 Visualisasi Grafik", "📋 Daftar Nilai Siswa", "📈 Kualitas Butir Soal"])
        
        with tab1:
            st.subheader("📈 Analisis Visual Hasil Tes")
            cg1, cg2 = st.columns(2)
            
            with cg1:
                fig_nilai = px.histogram(
                    df_hasil, x="Nilai", nbins=10,
                    title="<b>Distribusi Nilai Siswa</b>",
                    labels={"Nilai": "Rentang Nilai", "count": "Jumlah Siswa"},
                    color_discrete_sequence=['#4361ee']
                )
                fig_nilai.update_layout(bargap=0.05, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_nilai, use_container_width=True)
                
            with cg2:
                df_pie = analisis["Status_Soal"].value_counts().reset_index()
                fig_pie = px.pie(
                    df_pie, names="Status_Soal", values="count",
                    title="<b>Proporsi Kualitas Soal Keseluruhan</b>",
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            df_plot_soal = analisis.reset_index().rename(columns={"index": "Kode_Soal"})
            fig_soal = px.bar(
                df_plot_soal, x="Kode_Soal", y="Tingkat_Kesukaran",
                color="Kategori_Kesukaran",
                title="<b>Tingkat Kesukaran per Butir Soal</b>",
                labels={"Tingkat_Kesukaran": "Indeks Kesukaran (0 - 1)", "Kode_Soal": "Nomor Soal"},
                color_discrete_map={"Mudah 🟢": "#2ec4b6", "Sedang 🟡": "#ffb703", "Sukar 🔴": "#e63946"}
            )
            fig_soal.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_soal, use_container_width=True)
            
        with tab2:
            st.subheader("📋 Tabel Nilai Akhir Siswa")
            st.dataframe(df_hasil[["Nama", "Total_Benar", "Nilai"]].style.highlight_max(subset=['Nilai'], color='#d4edda'), use_container_width=True)
            
        with tab3:
            st.subheader("📋 Detail Parameter Analisis Soal")
            st.dataframe(analisis, use_container_width=True)
        
        # --- 8. TOMBOL DOWNLOAD EXCEL ---
        st.markdown("---")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_hasil.to_excel(writer, index=False, sheet_name='Nilai Siswa')
            analisis.to_excel(writer, sheet_name='Analisis Soal')
        
        st.download_button(
            label="📥 Unduh Laporan Lengkap (Excel)",
            data=output.getvalue(),
            file_name="Laporan_Analisis_Soal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}. Pastikan format file sesuai (Ada kolom 'Nama' dan 'Jawaban').")
else:
    st.info("👋 Silakan unggah file Excel/CSV di bilah samping (sidebar) sebelah kiri untuk memulai analisis.")