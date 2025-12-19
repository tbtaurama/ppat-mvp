import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import json
import io

# 1. Konfigurasi Halaman
st.set_page_config(page_title="AI Notaris Pro", page_icon="⚖️", layout="wide")
st.title("⚖️ AI Notaris - Spesialis Akta")

# 2. Sidebar Konfigurasi
with st.sidebar:
    st.header("🔑 Kunci Akses")
    api_key = st.text_input("Masukkan Gemini API Key", type="password")
    
    # --- FITUR DIAGNOSA (BARU) ---
    st.divider()
    st.markdown("### 🛠️ Menu Darurat")
    if st.button("Cek Koneksi & Daftar Model"):
        if not api_key:
            st.error("Masukkan API Key dulu!")
        else:
            try:
                genai.configure(api_key=api_key)
                st.write("Mencoba menghubungi Google...")
                list_model = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        list_model.append(m.name)
                st.success("Koneksi Berhasil! Model yang tersedia:")
                st.code(list_model)
            except Exception as e:
                st.error(f"Koneksi Gagal: {e}")

    if api_key:
        genai.configure(api_key=api_key)

# 3. Layout Input
col_template, col_space = st.columns([1, 1])

with col_template:
    st.subheader("1. Template Dokumen")
    uploaded_template = st.file_uploader("Upload File Word (.docx)", type="docx")

st.divider()
st.subheader("2. Upload Dokumen Para Pihak")

col_penjual, col_pembeli, col_aset = st.columns(3)

with col_penjual:
    st.markdown("### 👤 Pihak PENJUAL")
    files_penjual = st.file_uploader("KTP/NPWP Penjual", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="upl_penjual")

with col_pembeli:
    st.markdown("### 👤 Pihak PEMBELI")
    files_pembeli = st.file_uploader("KTP/NPWP Pembeli", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="upl_pembeli")

with col_aset:
    st.markdown("### 🏠 Dokumen ASET")
    files_aset = st.file_uploader("Sertifikat & PBB", type=["jpg", "png", "pdf"], accept_multiple_files=True, key="upl_aset")

# 4. Logic Pemrosesan
if st.button("🚀 Proses Pembuatan Akta", type="primary"):
    if not api_key:
        st.error("⚠️ API Key belum diisi!")
    elif not uploaded_template:
        st.error("⚠️ Template Word belum diupload!")
    elif not (files_penjual and files_pembeli and files_aset):
        st.error("⚠️ Semua dokumen (Penjual, Pembeli, Aset) wajib diisi!")
    else:
        with st.spinner('Sedang menganalisis dokumen...'):
            try:
                # --- UPDATE PENTING DISINI: NAMA MODEL DIGANTI ---
                # Menggunakan versi spesifik '001' yang lebih stabil
                model = genai.GenerativeModel('gemini-1.5-flash-001')
                
                request_content = []
                
                main_prompt = """
                BERTINDAKLAH SEBAGAI STAFF NOTARIS.
                Ekstrak data dari dokumen terlampir ke dalam JSON.
                Keys:
                {
                  "nama_penjual": "", "nik_penjual": "", "tempat_lahir_penjual": "", "tanggal_lahir_penjual": "", "pekerjaan_penjual": "", "alamat_penjual": "",
                  "nama_pembeli": "", "nik_pembeli": "", "pekerjaan_pembeli": "", "alamat_pembeli": "",
                  "no_sertifikat": "", "jenis_hak": "", "luas_tanah": "", "kelurahan": "", "kecamatan": "", "kabupaten": "",
                  "nop_pbb": "", "njop_total": "", "tahun_pajak": ""
                }
                ATURAN:
                1. Ambil data Penjual HANYA dari dokumen label 'PENJUAL'.
                2. Ambil data Pembeli HANYA dari dokumen label 'PEMBELI'.
                3. Tanggal format DD-MM-YYYY. Angka tanpa Rp/Titik.
                """
                request_content.append(main_prompt)

                request_content.append("\n\n--- PENJUAL ---\n")
                for f in files_penjual:
                    request_content.append({'mime_type': f.type, 'data': f.getvalue()})

                request_content.append("\n\n--- PEMBELI ---\n")
                for f in files_pembeli:
                    request_content.append({'mime_type': f.type, 'data': f.getvalue()})

                request_content.append("\n\n--- ASET ---\n")
                for f in files_aset:
                    request_content.append({'mime_type': f.type, 'data': f.getvalue()})

                response = model.generate_content(request_content)
                
                text_result = response.text.replace("```json", "").replace("```", "").strip()
                data_json = json.loads(text_result)
                
                st.success("✅ Analisis Selesai!")
                with st.expander("Lihat Hasil Bacaan AI"):
                    st.json(data_json)
                
                doc = DocxTemplate(uploaded_template)
                doc.render(data_json)
                
                bio = io.BytesIO()
                doc.save(bio)
                
                st.download_button(
                    label="⬇️ Download Akta (.docx)",
                    data=bio.getvalue(),
                    file_name="Akta_Final.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
                st.markdown("---")
                st.warning("Jika error '404 not found', coba klik tombol 'Cek Koneksi' di sidebar untuk melihat nama model yang benar.")
