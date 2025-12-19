import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from docxtpl import DocxTemplate
import json
import io
import re
import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem PPAT AI (AJB Lengkap)", page_icon="⚖️", layout="wide")
st.title("⚖️ Sistem Pembuatan AJB Otomatis")
st.markdown("Mendukung: Data Penjual, Pasangan, Pembeli, Surat Ukur, NIB, & Harga Transaksi.")

# --- FUNGSI PENDUKUNG ---
def clean_json_output(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

def terbilang(n):
    angka = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]
    if n < 12: return angka[n]
    elif n < 20: return terbilang(n - 10) + " belas"
    elif n < 100: return terbilang(n // 10) + " puluh " + terbilang(n % 10)
    elif n < 200: return "seratus " + terbilang(n - 100)
    elif n < 1000: return terbilang(n // 100) + " ratus " + terbilang(n % 100)
    elif n < 2000: return "seribu " + terbilang(n - 1000)
    elif n < 1000000: return terbilang(n // 1000) + " ribu " + terbilang(n % 1000)
    elif n < 1000000000: return terbilang(n // 1000000) + " juta " + terbilang(n % 1000000)
    elif n < 1000000000000: return terbilang(n // 1000000000) + " milyar " + terbilang(n % 1000000000)
    else: return "Angka terlalu besar"

def get_indo_date_info(tgl_obj):
    days = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
    months = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    return {
        "nama_hari": days[tgl_obj.weekday()],
        "tanggal_huruf": terbilang(tgl_obj.day).strip(),
        "nama_bulan": months[tgl_obj.month],
        "tahun_huruf": terbilang(tgl_obj.year).strip(),
        "full_date_angka": tgl_obj.strftime("%d-%m-%Y")
    }

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("1. Konfigurasi Sistem")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    st.header("2. Data Transaksi")
    tgl_akta = st.date_input("Tanggal Akta", datetime.date.today())
    nomor_akta = st.text_input("Nomor Akta", "01")
    
    # Input Harga Transaksi (Penting untuk AJB)
    harga_input = st.number_input("Harga Transaksi (Rp)", min_value=0, value=500000000, step=1000000)
    st.caption(f"Terbilang: {terbilang(int(harga_input))} rupiah")
    
    st.divider()
    st.header("3. Saksi Kantor")
    saksi_1 = st.text_input("Nama Saksi 1", "Budi, S.H.")
    saksi_2 = st.text_input("Nama Saksi 2", "Siti, S.H.")

    if api_key: genai.configure(api_key=api_key)

# --- HALAMAN UTAMA ---
col_kiri, col_kanan = st.columns([1, 1])

with col_kiri:
    st.subheader("Upload Template AJB")
    uploaded_template = st.file_uploader("Format .docx", type="docx")

with col_kanan:
    st.info("Pastikan Anda mengupload KTP Pasangan jika properti Harta Gono-Gini.")

st.divider()

# Area Upload Dokumen
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("##### 1. PENJUAL")
    f_penjual = st.file_uploader("KTP Penjual", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="p")
with c2:
    st.markdown("##### 2. PASANGAN (Opsional)")
    f_pasangan = st.file_uploader("KTP Suami/Istri", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="s")
with c3:
    st.markdown("##### 3. PEMBELI")
    f_pembeli = st.file_uploader("KTP Pembeli", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="b")
with c4:
    st.markdown("##### 4. ASET (Sertifikat & PBB)")
    f_aset = st.file_uploader("Sertifikat Tanah & PBB", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="a")

# --- TOMBOL PROSES ---
if st.button("🚀 GENERATE DRAF AJB", type="primary"):
    if not (api_key and uploaded_template and f_penjual and f_pembeli and f_aset):
        st.error("⚠️ Data belum lengkap! Cek API Key, Template, dan Dokumen Utama.")
    else:
        with st.spinner('AI sedang membaca KTP, Sertifikat (Surat Ukur/NIB), dan PBB...'):
            try:
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                req_content = []
                
                # --- PROMPT KHUSUS AJB ---
                prompt = """
                Ekstrak data legal dari dokumen terlampir ke format JSON.
                HILANGKAN BASA-BASI. OUTPUT HANYA JSON.
                
                TARGET DATA:
                {
                  "nama_penjual": "", "nik_penjual": "", "tempat_lahir_penjual": "", "tanggal_lahir_penjual": "", "pekerjaan_penjual": "", "alamat_penjual": "", "rt_penjual": "", "rw_penjual": "", "kel_penjual": "", "kec_penjual": "", "kab_penjual": "",
                  
                  "nama_pasangan": "", "nik_pasangan": "", "tempat_lahir_pasangan": "", "tanggal_lahir_pasangan": "", "pekerjaan_pasangan": "", "alamat_pasangan": "", "rt_pasangan": "", "rw_pasangan": "", "kel_pasangan": "", "kec_pasangan": "", "kab_pasangan": "",
                  
                  "nama_pembeli": "", "nik_pembeli": "", "tempat_lahir_pembeli": "", "tanggal_lahir_pembeli": "", "pekerjaan_pembeli": "", "alamat_pembeli": "", "rt_pembeli": "", "rw_pembeli": "", "kel_pembeli": "", "kec_pembeli": "", "kab_pembeli": "",
                  
                  "no_sertifikat": "", "nib": "", 
                  "no_surat_ukur": "", "tgl_surat_ukur": "",
                  "luas_tanah": "", 
                  "nop_pbb": "",
                  "lokasi_tanah": "", "kel_tanah": "", "kec_tanah": "", "kab_tanah": "", "provinsi_tanah": ""
                }
                
                ATURAN:
                1. Ambil data Penjual dari label 'PENJUAL', Pasangan dari 'PASANGAN', dst.
                2. Pecah alamat menjadi Jalan, RT, RW, Kelurahan, Kecamatan, Kab/Kota.
                3. Luas Tanah: HANYA ANGKA (contoh: 150).
                4. Tanggal Format: DD-MM-YYYY.
                """
                req_content.append(prompt)
                
                # Append Files
                req_content.append("\n\n--- PENJUAL ---\n")
                for f in f_penjual: req_content.append({'mime_type': f.type, 'data': f.getvalue()})
                
                if f_pasangan:
                    req_content.append("\n\n--- PASANGAN ---\n")
                    for f in f_pasangan: req_content.append({'mime_type': f.type, 'data': f.getvalue()})
                
                req_content.append("\n\n--- PEMBELI ---\n")
                for f in f_pembeli: req_content.append({'mime_type': f.type, 'data': f.getvalue()})
                
                req_content.append("\n\n--- ASET (CARI SURAT UKUR & NIB DISINI) ---\n")
                for f in f_aset: req_content.append({'mime_type': f.type, 'data': f.getvalue()})

                # Call AI
                safety = {HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE, HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE}
                response = model.generate_content(req_content, safety_settings=safety)
                
                # Process Data
                json_str = clean_json_output(response.text)
                final_data = json.loads(json_str)
                
                # Tambahkan Data Manual/Hitungan
                tgl_info = get_indo_date_info(tgl_akta)
                final_data.update(tgl_info)
                
                final_data['nomor_akta'] = nomor_akta
                final_data['tahun_akta'] = str(tgl_akta.year)
                final_data['harga_transaksi'] = "{:,.0f}".format(harga_input).replace(",", ".")
                final_data['harga_terbilang'] = terbilang(int(harga_input)).title()
                
                # Luas Terbilang (jika AI dapat angka luas)
                try:
                    luas_angka = int(re.sub(r'\D', '', str(final_data.get('luas_tanah', '0'))))
                    final_data['luas_terbilang'] = terbilang(luas_angka)
                except:
                    final_data['luas_terbilang'] = ".............."

                # Data Saksi
                final_data['nama_saksi_1'] = saksi_1
                final_data['nama_saksi_2'] = saksi_2

                st.success("✅ AJB Berhasil Dibuat!")
                with st.expander("Cek Data Hasil Ekstraksi"):
                    st.json(final_data)
                
                # Render Word
                doc = DocxTemplate(uploaded_template)
                doc.render(final_data)
                bio = io.BytesIO()
                doc.save(bio)
                
                st.download_button("⬇️ Download AJB Final (.docx)", bio.getvalue(), "AJB_Siap_Print.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
                
            except Exception as e:
                st.error(f"Error: {e}")
