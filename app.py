import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from supabase import create_client, Client

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Analisis Butir Soal", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.03);
    }
    .login-box {
        background-color: #ffffff; padding: 30px; border-radius: 10px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1); max-width: 450px; margin: auto;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KONEKSI SUPABASE & INITIALISASI ---
SUPABASE_URL = "https://nsyqohwdzvifjpdranse.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zeXFvaHdkenZpZmpwZHJhbnNlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1NzQ2NDYsImV4cCI6MjA5NjE1MDY0Nn0.5vmafEL4hOjtCwg3XUrSVVGOUuTFpLlDy_qURF1XJ5E"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Gagal terhubung ke database Supabase. Error: {e}")

# Inisialisasi Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "Gratis"
if "user_credits" not in st.session_state:
    st.session_state["user_credits"] = 0

# =========================================================================
# HALAMAN KHUSUS: UPDATE PASSWORD (DARI LINK EMAIL)
# =========================================================================
query_params = st.query_params
if "type" in query_params and query_params["type"] == "recovery":
    st.session_state["mode_reset_password"] = True

if st.session_state.get("mode_reset_password", False):
    st.markdown("<h1 style='text-align: center;'>🔄 Atur Ulang Password</h1>", unsafe_allow_html=True)
    st.divider()
    col_l, col_center, col_r = st.columns([1, 1.5, 1])
    with col_center:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.write("Silakan masukkan password baru Anda di bawah ini.")
        
        password_baru = st.text_input("Password Baru:", type="password", key="new_password_input")
        konfirmasi_password = st.text_input("Konfirmasi Password Baru:", type="password", key="confirm_new_password_input")
        
        btn_update_pass = st.button("Simpan Password Baru 💾", type="primary", use_container_width=True)
        
        if btn_update_pass:
            if len(password_baru) < 6:
                st.error("❌ Password harus minimal 6 karakter!")
            elif password_baru != konfirmasi_password:
                st.error("❌ Konfirmasi password tidak cocok!")
            else:
                try:
                    supabase.auth.update_user({"password": password_baru})
                    st.success("✅ Password berhasil diperbarui! Silakan klik 'Kembali ke Login'.")
                    st.session_state["mode_reset_password"] = False
                    st.query_params.clear()
                except Exception as e:
                    st.error(f"Gagal memperbarui password: {e}")
                    
        if st.button("Kembali ke Login", use_container_width=True):
            st.session_state["mode_reset_password"] = False
            st.query_params.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop() # Menghentikan kode di bawah agar tidak tumpah tindih dengan form login biasa

# =========================================================================
# HALAMAN 1: FORM LOGIN & REGISTRASI
# =========================================================================
if not st.session_state["logged_in"]:
    st.markdown("<h1 style='text-align: center;'>🎯 Sistem Analisis Butir Soal</h1>", unsafe_allow_html=True)
    st.divider()

    tab_login, tab_daftar = st.tabs(["🔐 Masuk Akun", "📝 Daftar Akun Baru"])
    
    with tab_login:
        col_l, col_center, col_r = st.columns([1, 1.5, 1])
        with col_center:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.subheader("Form Login")
            input_email = st.text_input("Email:", key="login_email")
            input_pass = st.text_input("Password:", type="password", key="login_pass")
            btn_login = st.button("Masuk Sekarang 🚀", use_container_width=True, type="primary")
            
            # --- FITUR LUPA PASSWORD ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔑 Lupa Password?"):
                st.caption("Masukkan email Anda di bawah ini untuk menerima tautan reset password.")
                email_reset = st.text_input("Email Terdaftar:", key="email_reset")
                btn_reset = st.button("Kirim Link Reset 📩", use_container_width=True)
                if btn_reset:
                    if email_reset.strip() == "":
                        st.warning("Silakan isi email terlebih dahulu!")
                    else:
                        try:
                            supabase.auth.reset_password_for_email(
                                email_reset, 
                                options={"redirect_to": "https://olah-nilai-mshaahezenmr.streamlit.app"}
                            )
                            st.success("✅ Tautan reset password telah dikirim ke email Anda!")
                        except Exception as e:
                            st.error(f"Gagal mengirim email reset: {e}")
            
            if btn_login:
                try:
                    response = supabase.auth.sign_in_with_password({"email": input_email, "password": input_pass})
                    if response.user:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = response.user.user_metadata.get("nama_lengkap", input_email)
                        st.session_state["user_role"] = response.user.user_metadata.get("role", "Gratis")
                        st.session_state["user_credits"] = int(response.user.user_metadata.get("credits", 10))
                        st.success("Login Berhasil!")
                        st.rerun()
                except Exception as e:
                    st.error("❌ Login Gagal. Periksa kembali email dan password Anda.")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_daftar:
        col_l, col_center, col_r = st.columns([1, 1.5, 1])
        with col_center:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.subheader("Buat Akun Baru")
            reg_name = st.text_input("Nama Lengkap:", key="reg_name")
            reg_email = st.text_input("Email Baru:", key="reg_email")
            reg_pass = st.text_input("Buat Password (Min 6 Karakter):", type="password", key="reg_pass")
            btn_daftar = st.button("Daftar Sekarang 📄", use_container_width=True, type="primary")
            
            if btn_daftar:
                if reg_name.strip() == "" or reg_email.strip() == "" or reg_pass.strip() == "":
                    st.error("⚠️ Semua kolom wajib diisi!")
                elif len(reg_pass) < 6:
                    st.error("⚠️ Password minimal 6 karakter.")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": reg_email,
                            "password": reg_pass,
                            "options": {
                                "data": {
                                    "nama_lengkap": reg_name,
                                    "role": "Gratis",
                                    "credits": 10
                                }
                            }
                        })
                        if response.user:
                            st.success(f"🎉 Pendaftaran Sukses! Silakan coba masuk di tab '🔐 Masuk Akun'.")
                    except Exception as e:
                        st.error(f"❌ Pendaftaran gagal. Detail: {e}")
            st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# HALAMAN 2: DASHBOARD UTAMA
# =========================================================================
else:
    with st.sidebar:
        st.subheader("👤 Profil Pengguna")
        st.write(f"Selamat Datang, **{st.session_state['username']}**")
        
        if st.session_state["user_role"] == "Premium":
            st.markdown("<span style='background-color:#d4edda; color:#155724; padding:4px 10px; border-radius:5px; font-weight:bold;'>⭐ AKUN PREMIUM (UNLIMITED)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='background-color:#fff3cd; color:#856404; padding:4px 10px; border-radius:5px; font-weight:bold;'>⚠️ AKUN GRATIS</span>", unsafe_allow_html=True)
            st.metric(label="🪙 Sisa Kredit Anda", value=f"{st.session_state['user_credits']} Kredit")
            st.caption("ℹ️ *Analisis data: 2 kredit per 45 siswa.*")
            st.caption("ℹ️ *Unduh File Excel: Biaya tambahan 2 kredit.*")
        
        if st.button("Keluar / Log Out 🏃‍♂️", type="secondary"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["user_role"] = "Gratis"
            st.session_state["user_credits"] = 0
            st.rerun()
            
        st.markdown("---")
        st.header("📋 1. Identitas Laporan")
        mata_pelajaran = st.text_input("Mata Pelajaran:", "Informatika")
        nama_guru = st.text_input("Nama Guru:", st.session_state["username"])
        
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
            df_template = pd.DataFrame({
                "Kelas Belajar": ["VIII A", "VIII A"], "Kelas Wali": ["VIII H", "VIII G"],
                "Nama": ["Budi", "Siti"], "Jawaban": ["ABBBBCCBCDACBAABBBBCBCBCCBBBCDCBCBBAACCC", "A-BBBCC--DACBAABB-BCBCBCCB-B-----B---C--"]
            })
            output_template = BytesIO()
            with pd.ExcelWriter(output_template, engine='xlsxwriter') as writer:
                df_template.to_excel(writer, index=False, sheet_name='Data Siswa')
            st.download_button(label="📄 Unduh Template Excel", data=output_template.getvalue(), file_name="Template_Data_Jawaban.xlsx")
            uploaded_file = st.file_uploader("Format: Excel / CSV", type=["xlsx", "csv"])

    st.title("🎯 Dashboard Analisis Butir Soal")
    st.markdown(f"**Mata Pelajaran:** {mata_pelajaran} &nbsp;&nbsp;|&nbsp;&nbsp; **Guru Pengampu:** {nama_guru}")
    st.divider()

    # --- PENGUMPULAN DATA ---
    df_mentah = None
    if metode_input == "📥 Unggah File Excel/CSV" and uploaded_file is not None:
        try:
            df_mentah = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df_mentah.columns = df_mentah.columns.str.strip()
            for c in df_mentah.columns:
                if "NAMA" in c.upper() and "Nama" not in df_mentah.columns: df_mentah = df_mentah.rename(columns={c: "Nama"})
                if "JAWABAN" in c.upper() and "Jawaban" not in df_mentah.columns: df_mentah = df_mentah.rename(columns={c: "Jawaban"})
            if "Kelas Belajar" not in df_mentah.columns: df_mentah["Kelas Belajar"] = "VII A"
            if "Kelas Wali" not in df_mentah.columns: df_mentah["Kelas Wali"] = "Umum"
        except Exception as e:
            st.error(f"Gagal membaca berkas: {e}")
            
    elif metode_input == "✍️ Ketik Langsung di Web":
        template_df = pd.DataFrame([{"Kelas Belajar": "VII A", "Kelas Wali": "Umum", "Nama": "", "Jawaban": ""}] * 5)
        edited_df = st.data_editor(template_df, num_rows="dynamic", use_container_width=True)
        df_bersih = edited_df[(edited_df["Nama"].str.strip() != "") & (edited_df["Jawaban"].str.strip() != "")]
        if not df_bersih.empty: df_mentah = df_bersih.copy()

    # --- PROSES UTAMA ---
    if df_mentah is not None and not df_mentah.empty:
        total_siswa = len(df_mentah)
        kredit_analisis = ( (total_siswa - 1) // 45 + 1 ) * 2
        
        st.success(f"📋 Data terdeteksi: **{total_siswa} Siswa**.")
        
        if "analisis_berjalan" not in st.session_state:
            st.session_state["analisis_berjalan"] = False

        # Cek Kredit untuk Tombol Analisis
        kredit_cukup_analisis = True
        if st.session_state["user_role"] != "Premium" and st.session_state["user_credits"] < kredit_analisis:
            kredit_cukup_analisis = False
            
        if not kredit_cukup_analisis:
            st.error(f"🚫 **Kredit Tidak Cukup untuk Analisis!** Dibutuhkan **{kredit_analisis} Kredit** (Sisa Anda: {st.session_state['user_credits']}).")
            pesan_wa = f"Halo Admin, saya ingin upgrade ke Premium karena kredit saya habis. Email: {st.session_state['username']}"
            link_wa = f"https://wa.me/6287749838193?text={pesan_wa.replace(' ', '%20')}"
            st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:12px;border-radius:5px;font-weight:bold;width:100%;cursor:pointer;">🟢 Hubungi Admin via WhatsApp untuk Upgrade Premium</button></a>', unsafe_allow_html=True)
        else:
            if st.button("🚀 Mulai Proses Analisis Data Sekarang", type="primary", use_container_width=True):
                if st.session_state["user_role"] != "Premium" and not st.session_state["analisis_berjalan"]:
                    baru_kredit = st.session_state["user_credits"] - kredit_analisis
                    try:
                        supabase.auth.update_user({"options": {"data": {"nama_lengkap": st.session_state["username"], "role": "Gratis", "credits": baru_kredit}}})
                        st.session_state["user_credits"] = baru_kredit
                        st.toast(f"🪙 Kredit terpotong {kredit_analisis} untuk analisis data!", icon="🪙")
                    except Exception as e:
                        st.error(f"Gagal memotong kredit: {e}")
                
                st.session_state["analisis_berjalan"] = True

            # JIKA PROSES ANALISIS DIAKTIFKAN
            if st.session_state["analisis_berjalan"]:
                try:
                    # PROSES HITUNG MATRIKS NILAI
                    matriks_skor = []
                    for _, row in df_mentah.iterrows():
                        skor_siswa = []
                        jawab = str(row["Jawaban"]).strip()
                        for i in range(jumlah_soal):
                            skor_siswa.append(1 if i < len(jawab) and jawab[i].upper() == kunci_jawaban[i].upper() else 0)
                        matriks_skor.append(skor_siswa)
                    
                    kolom_soal = [f"S_{i+1}" for i in range(jumlah_soal)]
                    df_skor = pd.DataFrame(matriks_skor, columns=kolom_soal)
                    df_hasil = pd.concat([df_mentah[["Kelas Belajar", "Kelas Wali", "Nama"]].reset_index(drop=True), df_skor], axis=1)
                    df_hasil["Total_Benar"] = df_skor.sum(axis=1)
                    df_hasil["Nilai"] = round((df_hasil["Total_Benar"] / jumlah_soal) * 100, 2)
                    
                    # PROSES ANALISIS KUALITAS SOAL
                    analisis = pd.DataFrame(index=kolom_soal)
                    analisis["Tingkat_Kesukaran"] = round(df_skor.mean(), 2)
                    analisis["Kategori_Kesukaran"] = analisis["Tingkat_Kesukaran"].apply(lambda p: "Sukar 🔴" if p < 0.3 else ("Sedang 🟡" if p <= 0.7 else "Mudah 🟢"))
                    
                    df_urut = df_hasil.sort_values(by="Total_Benar", ascending=False)
                    n_kel = max(1, len(df_urut) // 2)
                    analisis["Daya_Pembeda"] = round(df_urut.iloc[:n_kel][kolom_soal].mean() - df_urut.iloc[-n_kel:][kolom_soal].mean(), 2)
                    
                    def pemetaan_daya_pembeda(dp):
                        if dp <= 0:
                            return "🚨 Invalid / Malfungsi (Rekomendasi: Eliminasi atau Konstruksi Ulang)"
                        elif dp <= 0.2:
                            return "⚠️ Daya Pembeda Rendah (Rekomendasi: Revisi Total Narasi & Pilihan Ganda)"
                        elif dp <= 0.4:
                            return "🆗 Cukup Optimal (Rekomendasi: Dapat Digunakan dengan Refinement Ringan)"
                        elif dp <= 0.7:
                            return "👍 Kualitas Baik (Rekomendasi: Sangat Layak Masuk Bank Soal Utama)"
                        else:
                            return "🌟 Kualitas Prima (Rekomendasi: Standar Mutu Sempurna, Pertahankan!)"
                            
                    analisis["Status_Soal"] = analisis["Daya_Pembeda"].apply(pemetaan_daya_pembeda)

                    # KREASI DESKRIPSI EVALUASI OTOMATIS (DINAMIS)
                    avg_nilai = df_hasil['Nilai'].mean()
                    total_prima_baik = len(analisis[analisis["Daya_Pembeda"] > 0.4])
                    total_butir = len(analisis)
                    
                    narasi_hasil_belajar = f"Berdasarkan hasil evaluasi pada mata pelajaran {mata_pelajaran}, kelas menunjukkan performa rata-rata dengan nilai {avg_nilai:.1f}. Nilai tertinggi mencapai {df_hasil['Nilai'].max()} dan nilai terendah berada pada angka {df_hasil['Nilai'].min()}. "
                    if avg_nilai >= 75:
                        narasi_hasil_belajar += "Secara umum, tingkat ketuntasan klasikal dan pemahaman siswa terhadap materi instrumen ini berkategori SANGAT TINGGI/BAIK."
                    elif avg_nilai >= 60:
                        narasi_hasil_belajar += "Secara umum, mayoritas siswa menunjukkan penguasaan materi berskala MENENGAH. Diperlukan penguatan atau remedial parsial pada topik tertentu."
                    else:
                        narasi_hasil_belajar += "Secara agregat, capaian kelas berada di bawah standar ketuntasan ideal. Direkomendasikan evaluasi menyeluruh pada strategi pembelajaran guru."

                    narasi_kualitas_soal = f"Dari total {total_butir} butir soal yang diuji, terdapat {total_prima_baik} butir soal ({int(total_prima_baik/total_butir*100)}%) yang terverifikasi memiliki parameter validitas daya pembeda yang BAIK hingga PRIMA sehingga sangat layak dipertahankan di bank soal utama. Sisanya membutuhkan konstruksi narasi ulang atau peninjauan ulang pada opsi pengecoh (distraktor)."

                    # TAMPILAN ELEMEN GRAFIK & DATA DI WEB
                    st.subheader("📊 Ringkasan Hasil Analisis")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Total Siswa", f"{len(df_hasil)} Orang")
                    c2.metric("Rata-rata Nilai", f"{round(avg_nilai, 1)}")
                    c3.metric("Nilai Tertinggi", f"{df_hasil['Nilai'].max()}")
                    c4.metric("Nilai Terendah", f"{df_hasil['Nilai'].min()}")
                    
                    st.info(f"📝 **Deskripsi Hasil Ulangan Kelas:**\n{narasi_hasil_belajar}")
                    st.info(f"📈 **Deskripsi Mutu Instrumen Soal:**\n{narasi_kualitas_soal}")
                    
                    tab1, tab2, tab3 = st.tabs(["📊 Visualisasi Grafik", "📋 Daftar Nilai Siswa", "📈 Kualitas Butir Soal"])
                    with tab1:
                        cg1, cg2 = st.columns(2)
                        with cg1: st.plotly_chart(px.histogram(df_hasil, x="Nilai", nbins=10, title="<b>Distribusi Nilai Siswa</b>"), use_container_width=True)
                        with cg2: st.plotly_chart(px.pie(analisis["Status_Soal"].value_counts().reset_index(), names="Status_Soal", values="count", title="<b>Proporsi Kualitas Soal</b>"), use_container_width=True)
                    with tab2: st.dataframe(df_hasil[["Kelas Belajar", "Kelas Wali", "Nama", "Total_Benar", "Nilai"]], use_container_width=True)
                    with tab3: st.dataframe(analisis, use_container_width=True)
                    
                    # =========================================================
                    # 🔒 LOGIKA HAK DOWNLOAD & PEMOTONGAN KREDIT
                    # =========================================================
                    st.markdown("---")
                    st.subheader("📥 Fitur Unduh Dokumen Laporan")
                    
                    # PEMBUATAN EXCEL GENERATOR (PRINT READY FORMAT A4)
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        workbook  = writer.book
                        
                        # FORMATTING STYLES
                        title_fmt = workbook.add_format({'bold': True, 'font_size': 15, 'font_color': '#1E3A8A'})
                        subtitle_fmt = workbook.add_format({'font_size': 10, 'italic': True, 'font_color': '#555555'})
                        header_fmt = workbook.add_format({
                            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
                            'fg_color': '#1E3A8A', 'font_color': 'white', 'border': 1, 'font_size': 10
                        })
                        meta_label_fmt = workbook.add_format({'bold': True, 'bg_color': '#F1F5F9', 'border': 1, 'font_size': 10})
                        meta_val_fmt = workbook.add_format({'align': 'left', 'border': 1, 'font_size': 10})
                        cell_border_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter', 'font_size': 10})
                        cell_center_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center', 'font_size': 10})
                        cell_num_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter', 'align': 'right', 'num_format': '0.00', 'font_size': 10})
                        desc_title_fmt = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': '#1E3A8A', 'bg_color': '#E2E8F0'})
                        desc_text_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_size': 10, 'italic': True})
                        
                        # -----------------------------------------------------
                        # LEMBAR 1: RINGKASAN & GRAFIK (SET PRINT READY A4)
                        # -----------------------------------------------------
                        ws_summary = workbook.add_worksheet('Ringkasan & Grafik')
                        
                        # --- CONFIG PAGE SETUP UNTUK OTOMATIS CETAK A4 ---
                        ws_summary.set_paper(9) # Kode angka 9 merepresentasikan Kertas A4 standar internasional
                        ws_summary.set_landscape() # Mengatur layout ke tidur/horizontal agar grafik muat rapi
                        ws_summary.set_margins(left=0.5, right=0.5, top=0.5, bottom=0.5) # Mengecilkan margin agar ruang cetak luas
                        ws_summary.fit_to_pages(1, 1) # MEMAKSA semua elemen pas masuk ke dalam halaman cetak
                        ws_summary.set_print_scale(100)
                        
                        # Judul Dokumen
                        ws_summary.write('B2', 'LAPORAN EKSEKUTIF ANALISIS BUTIR SOAL', title_fmt)
                        ws_summary.write('B3', 'Sistem Evaluasi Mutu Soal Otomatis Berbasis Data', subtitle_fmt)
                        
                        # Identitas Laporan
                        ws_summary.write('B5', 'Mata Pelajaran', meta_label_fmt)
                        ws_summary.write('C5', mata_pelajaran, meta_val_fmt)
                        ws_summary.write('B6', 'Guru Pengampu', meta_label_fmt)
                        ws_summary.write('C6', nama_guru, meta_val_fmt)
                        ws_summary.write('B7', 'Jumlah Butir Soal', meta_label_fmt)
                        ws_summary.write('C7', jumlah_soal, cell_center_fmt)
                        ws_summary.write('B8', 'Total Responden', meta_label_fmt)
                        ws_summary.write('C8', f"{len(df_hasil)} Siswa", cell_center_fmt)
                        
                        # Statistik Deskriptif
                        ws_summary.write('B10', 'Rata-rata Nilai', meta_label_fmt)
                        ws_summary.write('C10', df_hasil['Nilai'].mean(), cell_num_fmt)
                        ws_summary.write('B11', 'Nilai Tertinggi', meta_label_fmt)
                        ws_summary.write('C11', df_hasil['Nilai'].max(), cell_num_fmt)
                        ws_summary.write('B12', 'Nilai Terendah', meta_label_fmt)
                        ws_summary.write('C12', df_hasil['Nilai'].min(), cell_num_fmt)
                        
                        # BLOK TAMBAHAN: DESKRIPSI & EVALUASI DI EXCEL (Dimerge agar muat narasi panjang)
                        ws_summary.merge_range('B15:C15', ' 📝 DESKRIPSI HASIL BELAJAR KELAS', desc_title_fmt)
                        ws_summary.merge_range('B16:C19', narasi_hasil_belajar, desc_text_fmt)
                        
                        ws_summary.merge_range('B21:C21', ' 📈 DESKRIPSI EVALUASI MUTU INSTRUMEN', desc_title_fmt)
                        ws_summary.merge_range('B22:C25', narasi_kualitas_soal, desc_text_fmt)
                        
                        ws_summary.set_column('B:B', 22)
                        ws_summary.set_column('C:C', 26)
                        
                        # DATA BACKEND GRAFIK EXCEL
                        ws_chart_data = workbook.add_worksheet('Data_Grafik_Kalkulasi')
                        
                        # Generate Chart 1: Proporsi Kualitas Soal (Pie)
                        status_counts = analisis["Status_Soal"].value_counts()
                        ws_chart_data.write('A1', 'Status Kualitas', header_fmt)
                        ws_chart_data.write('B1', 'Jumlah Soal', header_fmt)
                        for idx, (lbl, val) in enumerate(status_counts.items(), start=1):
                            ws_chart_data.write(idx, 0, lbl)
                            ws_chart_data.write(idx, 1, val)
                            
                        chart_pie = workbook.add_chart({'type': 'pie'})
                        chart_pie.add_series({
                            'name': 'Proporsi Kualitas Soal',
                            'categories': f'=Data_Grafik_Kalkulasi!$A$2:$A${len(status_counts)+1}',
                            'values':     f'=Data_Grafik_Kalkulasi!$B$2:$B${len(status_counts)+1}',
                            'data_labels': {'percentage': True, 'value': False, 'position': 'outside_end'},
                        })
                        chart_pie.set_title({'name': 'Proporsi Kualitas Soal'})
                        chart_pie.set_size({'width': 440, 'height': 260})
                        ws_summary.insert_chart('E4', chart_pie)
                        
                        # Generate Chart 2: Distribusi Nilai (Column)
                        bins_interval = [0, 20, 40, 60, 80, 100]
                        labels_interval = ['0-20', '21-40', '41-60', '61-80', '81-100']
                        df_hasil['Interval_Nilai'] = pd.cut(df_hasil['Nilai'], bins=bins_interval, labels=labels_interval, include_lowest=True)
                        bin_counts = df_hasil['Interval_Nilai'].value_counts().reindex(labels_interval, fill_value=0)
                        
                        ws_chart_data.write('D1', 'Interval Nilai', header_fmt)
                        ws_chart_data.write('E1', 'Frekuensi Siswa', header_fmt)
                        for idx, (lbl, val) in enumerate(bin_counts.items(), start=1):
                            ws_chart_data.write(idx, 3, lbl)
                            ws_chart_data.write(idx, 4, val)
                            
                        chart_bar = workbook.add_chart({'type': 'column'})
                        chart_bar.add_series({
                            'name': 'Jumlah Siswa',
                            'categories': '=Data_Grafik_Kalkulasi!$D$2:$D$6',
                            'values':     '=Data_Grafik_Kalkulasi!$E$2:$E$6',
                            'data_labels': {'value': True},
                        })
                        chart_bar.set_title({'name': 'Grafik Distribusi Capaian Nilai Siswa'})
                        chart_bar.set_legend({'none': True})
                        chart_bar.set_size({'width': 440, 'height': 240})
                        ws_summary.insert_chart('E17', chart_bar)
                        
                        # -----------------------------------------------------
                        # LEMBAR 2: DAFTAR NILAI SISWA (PRINT READY A4)
                        # -----------------------------------------------------
                        df_excel_siswa = df_hasil.drop(columns=['Interval_Nilai'], errors='ignore')
                        df_excel_siswa.to_excel(writer, sheet_name='Daftar Nilai Siswa', index=False, startrow=4, header=False)
                        ws_siswa = writer.sheets['Daftar Nilai Siswa']
                        
                        # Konfigurasi Cetak Kertas Otomatis Lembar Nilai
                        ws_siswa.set_paper(9) # Kertas A4
                        ws_siswa.set_landscape() # Landscape agar seluruh soal muat horizontal
                        ws_siswa.set_margins(0.4, 0.4, 0.5, 0.5)
                        ws_siswa.fit_to_pages(1, 0) # Pas ke dalam 1 halaman lebar kertas, biarkan baris memanjang ke bawah
                        
                        ws_siswa.write('A2', 'REKAPITULASI CAPAIAN DAN MATRIKS JAWABAN SISWA', title_fmt)
                        
                        for col_num, col_name in enumerate(df_excel_siswa.columns):
                            ws_siswa.write(4, col_num, col_name, header_fmt)
                            
                        for col_num, col_name in enumerate(df_excel_siswa.columns):
                            max_len = max(df_excel_siswa[col_name].astype(str).map(len).max(), len(col_name)) + 3
                            ws_siswa.set_column(col_num, col_num, max_len)
                            
                        total_cols = len(df_excel_siswa.columns)
                        ws_siswa.set_column(0, 2, 15, cell_border_fmt)       
                        ws_siswa.set_column(3, total_cols-3, 5, cell_center_fmt) 
                        ws_siswa.set_column(total_cols-2, total_cols-2, 12, cell_center_fmt) 
                        ws_siswa.set_column(total_cols-1, total_cols-1, 12, cell_num_fmt)    
                        
                        # -----------------------------------------------------
                        # LEMBAR 3: KUALITAS BUTIR SOAL (PRINT READY A4)
                        # -----------------------------------------------------
                        df_excel_soal = analisis.reset_index().rename(columns={'index': 'Butir Soal'})
                        df_excel_soal.to_excel(writer, sheet_name='Kualitas Butir Soal', index=False, startrow=4, header=False)
                        ws_soal = writer.sheets['Kualitas Butir Soal']
                        
                        # Konfigurasi Cetak Kertas Otomatis Lembar Analisis Soal
                        ws_soal.set_paper(9) # Kertas A4
                        ws_soal.set_portrait() # Portrait karena kolom sedikit namun baris memanjang ke bawah
                        ws_soal.set_margins(0.5, 0.5, 0.5, 0.5)
                        ws_soal.fit_to_pages(1, 0) # Pas lebar halaman kertas
                        
                        ws_soal.write('A2', 'EVALUASI PARAMETER DAN KUALITAS VALIDITAS BUTIR SOAL', title_fmt)
                        
                        for col_num, col_name in enumerate(df_excel_soal.columns):
                            ws_soal.write(4, col_num, col_name, header_fmt)
                            
                        for col_num, col_name in enumerate(df_excel_soal.columns):
                            max_len = max(df_excel_soal[col_name].astype(str).map(len).max(), len(col_name)) + 4
                            ws_soal.set_column(col_num, col_num, max_len)
                            
                        ws_soal.set_column(0, 0, 12, cell_center_fmt) 
                        ws_soal.set_column(1, 1, 16, cell_num_fmt)    
                        ws_soal.set_column(2, 2, 20, cell_border_fmt) 
                        ws_soal.set_column(3, 3, 14, cell_num_fmt)    
                        ws_soal.set_column(4, 4, 60, cell_border_fmt) 
                        
                    excel_data = output.getvalue()
                    
                    # Logika Hak Download Konten Premium/Gratis
                    if st.session_state["user_role"] == "Premium":
                        st.download_button(
                            label="📥 Unduh Laporan Lengkap Excel (Gratis Akun Premium)", 
                            data=excel_data, 
                            file_name=f"Analisis_Siap_Print_{mata_pelajaran.replace(' ','_')}.xlsx", 
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.info("🪙 *Mengunduh berkas laporan format A4 otomatis ini memotong 2 kredit.*")
                        if st.session_state["user_credits"] < 2:
                            st.warning(f"⚠️ **Kredit Anda Habis!**")
                            pesan_wa = f"Halo Admin, saya ingin upgrade ke Premium karena kredit unduhan saya habis. Email: {st.session_state['username']}"
                            link_wa = f"https://wa.me/6281234567890?text={pesan_wa.replace(' ', '%20')}"
                            st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:12px;border-radius:5px;font-weight:bold;width:100%;cursor:pointer;">🟢 Hubungi Admin via WhatsApp untuk Upgrade Premium (Unlimited)</button></a>', unsafe_allow_html=True)
                        else:
                            def proses_potong_kredit_download():
                                kredit_baru_dl = st.session_state["user_credits"] - 2
                                try:
                                    supabase.auth.update_user({"options": {"data": {"nama_lengkap": st.session_state["username"], "role": "Gratis", "credits": kredit_baru_dl}}})
                                    st.session_state["user_credits"] = kredit_baru_dl
                                except Exception as e:
                                    st.error(f"Gagal memotong kredit unduhan: {e}")

                            st.download_button(
                                label=f"📥 Unduh Laporan Lengkap Excel (Potong 2 Kredit)", 
                                data=excel_data, 
                                file_name=f"Analisis_Siap_Print_{mata_pelajaran.replace(' ','_')}.xlsx", 
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                type="primary",
                                use_container_width=True,
                                on_click=proses_potong_kredit_download
                            )
                            
                except Exception as e:
                    st.error(f"Terjadi kesalahan analisis: {e}")
    else:
        st.info("👋 Silakan masukkan data siswa terlebih dahulu di bilah samping (sidebar).")
