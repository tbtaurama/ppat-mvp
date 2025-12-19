import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import json
import io

# 1. Konfigurasi Halaman
st.set_page_config(page_title="AI Notaris Pro", page_icon="⚖️", layout="wide")

st.title("⚖️ AI Notaris - Spesialis Akta")
st.markdown("Sistem pemisah data Penjual & Pembeli otomatis.")

# 2. Sidebar Konfigurasi
with st.sidebar:
    st.header("🔑 Kunci Akses")
    api_key = st.text_input("Masukkan Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    st.info("💡 **Tips:** Upload file terpisah agar AI tidak bingung mana Penjual dan mana Pembeli.")

# 3. Layout Input (Menggunakan Kolom agar Rapi)
col_template, col_space = st.columns([1, 1])

with col_template:
    st.subheader("1. Template Dokumen")
    uploaded_template = st.file_uploader("Upload File Word (.docx)", type="docx")

st.divider()

st.subheader("2. Upload Dokumen Para Pihak")

# Membuat 3 Kolom untuk Upload Dokumen Terpisah
col_penjual, col_pembeli, col_aset = st.columns(3)

with col_penjual:
    st.markdown("### 👤 Pihak PENJUAL")
    files_penjual = st.file_uploader(
        "Upload KTP/NPWP Penjual", 
        type=["jpg", "png", "pdf"], 
        accept_multiple_files=True,
        key="upl_penjual"
    )

with col_pembeli:
    st.markdown("### 👤 Pihak PEMBELI")
    files_pembeli = st.file_uploader(
        "Upload KTP/NPWP Pembeli", 
        type=["jpg", "png", "pdf"], 
        accept_multiple_files=True,
        key="upl_pembeli"
    )

with col_aset:
    st.markdown("### 🏠 Dokumen ASET")
    files_aset = st.file_uploader(
        "Sertifikat & PBB", 
        type=["jpg", "png", "pdf"], 
        accept_multiple_files=True,
        key="upl_aset"
    )

# 4. Logic Pemrosesan
if st.button("🚀 Proses Pembuatan Akta", type="primary"):
    # Validasi Kelengkapan
    if not api_key:
        st.error("⚠️ API Key belum diisi!")
    elif not uploaded_template:
        st.error("⚠️ Template Word belum diupload!")
    elif not files_penjual:
        st.error("⚠️ Data PENJUAL wajib ada!")
    elif not files_pembeli:
        st.error("⚠️ Data PEMBELI wajib ada!")
    elif not files_aset:
        st.error("⚠️ Data ASET (Sertifikat/PBB) wajib ada!")
    else:
        with st.spinner('Sedang menganalisis dokumen satu per satu...'):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # --- TEKNIK CONTEXT MARKER ---
                # Kita akan menyusun list pesan untuk dikirim ke AI
                # dengan memberi "Label Teks" sebelum gambar, agar AI tahu konteksnya.
                
                request_content = []
                
                # A. Instruksi Utama (System Prompt)
                main_prompt = """
                BERTINDAKLAH SEBAGAI STAFF NOTARIS PROFESIONAL.
                
                TUGAS:
                Ekstrak data dari dokumen yang saya berikan berurutan di bawah ini.
                Saya sudah memisahkan mana dokumen PENJUAL, mana PEMBELI, dan mana ASET.
                
                OUTPUT JSON HARUS MEMILIKI KEYS BERIKUT (Isi string kosong jika tidak terbaca):
                {
                  "nama_penjual": "", "nik_penjual": "", "tempat_lahir_penjual": "", "tanggal_lahir_penjual": "", "pekerjaan_penjual": "", "alamat_penjual": "",
                  "nama_pembeli": "", "nik_pembeli": "", "pekerjaan_pembeli": "", "alamat_pembeli": "",
                  "no_sertifikat": "", "jenis_hak": "", "luas_tanah": "", "kelurahan": "", "kecamatan": "", "kabupaten": "",
                  "nop_pbb": "", "njop_total": "", "tahun_pajak": ""
                }
