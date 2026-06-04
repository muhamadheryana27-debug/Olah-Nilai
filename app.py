import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Analisis Butir Soal", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.03);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR: PENGATURAN & PILIHAN INPUT ---
with st.sidebar:
    # --- FITUR BARU: IDENTITAS ---
    st.header("📋 1. Identitas")
    mata_pelajaran = st.text_input("Mata Pelajaran:", "Informatika")
    nama_guru = st.text_input("Nama Guru:", "Bapak/Ibu Guru")
    
    st.markdown("---")
    st.header("⚙️ 2. Pengaturan Soal")
    kunci_jawaban = st.text_input("Ketik Kunci Jawaban:", "ABBBBCCBCDACBAABBBBCBCBCCBBBCDCBCBBAACCC")
    jumlah_soal = len(kunci_jawaban.replace("-", "").strip())
    st.info(f"📌 **Jumlah Soal:** {jumlah_soal} butir")
    
    st.markdown("---")
    st.header("📂 3. Sumber Data Siswa")
    metode_input = st.radio("Pilih metode pengisian:", ["✍️ Ketik Langsung di Web", "📥 Unggah File Excel/CSV"])
    
    uploaded_file = None
    if metode_input == "📥 Unggah File Excel/CSV":
        st.info("💡 Belum punya format excelnya? Unduh template di bawah ini:")
        
        df_template = pd.DataFrame({
            "Kelas Belajar": ["VIII A", "VIII A", "VIII A"],
            "Kelas Wali": ["VIII H", "VIII G", "VIII H"],
            "Nama": ["Budi", "Siti", "Agus"],
            "Jawaban": [
                "ABBBBCCBCDACBAABBBBCBCBCCBBBCDCBCBBAACCC",
                "A-BBBCC--DACBAABB-BCBCBCCB-B-----B---C--",
                "ABBBB--------AABB-B--C---B----CBCB--AC-C"
            ]
        })
        
        output_template = BytesIO()
        with pd.ExcelWriter(output_template, engine='xlsxwriter') as writer:
            df_template.to_excel(writer, index=False, sheet_name='Data Siswa')
            worksheet = writer.sheets['Data Siswa']
            worksheet.set_column('A:B', 15)
            worksheet.set_column('C:C', 25)
            worksheet.set_column('D:D', 50)
            
        st.download_button(
            label="📄 Unduh Template Excel",
            data=output_template.getvalue(),
            file_name="Template_Data_Jawaban.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown("---")
        
        st.warning("Pastikan file memiliki kolom: **Kelas Belajar**, **Kelas Wali**, **Nama**, dan **Jawaban**")
        uploaded_file = st.file_uploader("Format: Excel / CSV", type=["xlsx", "csv"])

# --- 4. HEADER DASHBOARD ---
st.title("🎯 Dashboard Analisis Butir Soal")
# --- FITUR BARU: MENAMPILKAN IDENTITAS DI DASHBOARD ---
st.markdown(f"**Mata Pelajaran:** {mata_pelajaran} &nbsp;&nbsp;|&nbsp;&nbsp; **Guru Pengampu:** {nama_guru}")
st.divider()

# --- 5. LOGIKA PENGUMPULAN DATA ---
df_mentah = None

if metode_input == "📥 Unggah File Excel/CSV":
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df_mentah = pd.read_csv(uploaded_file)
        else:
            df_mentah = pd.read_excel(uploaded_file)
            
        if "Kelas Belajar" not in df_mentah.columns:
            df_mentah.insert(0, "Kelas Belajar", "Tanpa Kelas Belajar")
        if "Kelas Wali" not in df_mentah.columns:
            df_mentah.insert(1, "Kelas Wali", df_mentah["Kelas Belajar"])
            
        with st.expander("👀 Lihat Pratinjau Data Mentah"):
            st.dataframe(df_mentah.head(), use_container_width=True)

elif metode_input == "✍️ Ketik Langsung di Web":
    st.subheader("✍️ Tabel Input Jawaban Siswa")
    
    template_df = pd.DataFrame([{"Kelas Belajar": "", "Kelas Wali": "", "Nama": "", "Jawaban": ""}] * 5)
    edited_df = st.data_editor(template_df, num_rows="dynamic", use_container_width=True)
    
    df_bersih = edited_df[(edited_df["Nama"].str.strip() != "") & (edited_df["Jawaban"].str.strip() != "")]
    if not df_bersih.empty:
        df_bersih["Kelas Belajar"] = df_bersih["Kelas Belajar"].replace("", "Tanpa Kelas")
        df_bersih["Kelas Wali"] = df_bersih["Kelas Wali"].replace("", "Tanpa Kelas")
        df_mentah = df_bersih.copy()

# --- 6. FITUR FILTER FLEKSIBEL ---
df_filter = None
kelas_terpilih = "Semua Data"
kolom_fokus = "Kelas Belajar"

if df_mentah is not None and not df_mentah.empty:
    st.divider()
    st.subheader("🔍 Mode Analisis & Filter Kelas")
    
    col_mode, col_filter = st.columns([1, 2])
    with col_mode:
        kolom_fokus = st.radio("Fokuskan Analisis Berdasarkan:", ["Kelas Belajar", "Kelas Wali"])
        
    with col_filter:
        daftar_kelas = df_mentah[kolom_fokus].astype(str).unique().tolist()
        daftar_kelas.sort()
        pilihan = ["Semua " + kolom_fokus] + daftar_kelas
        kelas_terpilih = st.selectbox(f"Pilih {kolom_fokus}:", pilihan)
    
    if kelas_terpilih.startswith("Semua "):
        df_filter = df_mentah.copy()
        kelas_terpilih = "Semua Data"
    else:
        df_filter = df_mentah[df_mentah[kolom_fokus] == kelas_terpilih].copy()

# --- 7. PROSES ANALISIS UTAMA ---
if df_filter is not None and not df_filter.empty and jumlah_soal > 0:
    try:
        with st.spinner("Menganalisis data..."):
            matriks_skor = []
            for index, row in df_filter.iterrows():
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
            df_hasil = pd.concat([df_filter[["Kelas Belajar", "Kelas Wali", "Nama"]].reset_index(drop=True), df_skor], axis=1)
            
            df_hasil["Total_Benar"] = df_skor.sum(axis=1)
            df_hasil["Nilai"] = round((df_hasil["Total_Benar"] / jumlah_soal) * 100, 2)
            
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

        # --- TAMPILAN DASHBOARD METRICS ---
        st.subheader(f"📊 Ringkasan: {kelas_terpilih}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Siswa", f"{len(df_hasil)} Orang")
        col2.metric("Rata-rata Nilai", f"{round(df_hasil['Nilai'].mean(), 1)}")
        col3.metric("Nilai Tertinggi", f"{df_hasil['Nilai'].max()}")
        col4.metric("Nilai Terendah", f"{df_hasil['Nilai'].min()}")
        
        st.divider()
        
        # --- TAMPILAN TAB INTERAKTIF ---
        tab1, tab2, tab3 = st.tabs(["📊 Visualisasi Grafik", "📋 Daftar Nilai Siswa", "📈 Kualitas Butir Soal"])
        
        with tab1:
            st.subheader(f"📈 Analisis Visual Hasil Tes - {kelas_terpilih}")
            cg1, cg2 = st.columns(2)
            
            with cg1:
                fig_nilai = px.histogram(df_hasil, x="Nilai", nbins=10, title="<b>Distribusi Nilai Siswa</b>", labels={"Nilai": "Rentang Nilai", "count": "Jumlah Siswa"}, color_discrete_sequence=['#4361ee'])
                fig_nilai.update_layout(bargap=0.05, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_nilai, use_container_width=True)
                
            with cg2:
                df_pie = analisis["Status_Soal"].value_counts().reset_index()
                fig_pie = px.pie(df_pie, names="Status_Soal", values="count", title="<b>Proporsi Kualitas Soal</b>", color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            df_plot_soal = analisis.reset_index().rename(columns={"index": "Kode_Soal"})
            fig_soal = px.bar(df_plot_soal, x="Kode_Soal", y="Tingkat_Kesukaran", color="Kategori_Kesukaran", title="<b>Tingkat Kesukaran per Butir Soal</b>", color_discrete_map={"Mudah 🟢": "#2ec4b6", "Sedang 🟡": "#ffb703", "Sukar 🔴": "#e63946"})
            fig_soal.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_soal, use_container_width=True)
            
        with tab2:
            st.subheader(f"📋 Tabel Nilai Akhir Siswa - {kelas_terpilih}")
            st.dataframe(df_hasil[["Kelas Belajar", "Kelas Wali", "Nama", "Total_Benar", "Nilai"]].style.highlight_max(subset=['Nilai'], color='#d4edda'), use_container_width=True)
            
        with tab3:
            st.subheader(f"📋 Detail Parameter Analisis Soal - {kelas_terpilih}")
            st.dataframe(analisis, use_container_width=True)
        
        # --- TOMBOL DOWNLOAD EXCEL ---
        st.markdown("---")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_hasil.to_excel(writer, index=False, sheet_name='Nilai Siswa')
            analisis.to_excel(writer, sheet_name='Analisis Soal')
        
        # --- FITUR BARU: NAMA FILE EXCEL OTOMATIS BERDASARKAN MAPEL & KELAS ---
        nama_file_mapel = mata_pelajaran.replace(" ", "_")
        nama_file_kelas = kelas_terpilih.replace(" ", "_")
        nama_file_final = f"Analisis_{nama_file_mapel}_{nama_file_kelas}.xlsx"
        
        st.download_button(
            label=f"📥 Unduh Laporan ({kelas_terpilih})", 
            data=output.getvalue(), 
            file_name=nama_file_final, 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            type="primary"
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data. Detail Error: {e}")
else:
    if metode_input == "✍️ Ketik Langsung di Web":
        st.info("👋 Silakan mulai mengetik Kelas Belajar, Kelas Wali, Nama, dan Jawaban siswa pada tabel di atas.")
    else:
        st.info("👋 Silakan unggah file Excel/CSV untuk memulai analisis.")