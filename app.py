import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
import json
import io

# 1. Konfigurasi Halaman Website
st.set_page_config(page_title="AI Notaris MVP", page_icon="⚖️")

st.title("⚖️ AI Notaris - Auto Drafting (PDF Support)")
st.markdown("Upload dokumen (Gambar/PDF), biarkan AI mengisi draf Akta Anda.")

# 2. Sidebar untuk API Key
with st.sidebar:
    st.header("Konfigurasi")
    api_key = st.text_input("Masukkan Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    st.info("Tips: Anda bisa upload campuran file (misal: KTP format JPG, Sertifikat format PDF).")

# 3. Area Upload File
col1, col2 = st.columns(2)
with col1:
    uploaded_template = st.file_uploader("1. Upload Template Word (.docx)", type="docx")
with col2:
    # UPDATE: Menambahkan 'pdf' ke dalam daftar tipe file
    uploaded_files = st.file_uploader(
        "2. Upload Dokumen (KTP/Sertifikat/PBB)", 
        type=["jpg", "jpeg", "png", "pdf"], 
        accept_multiple_files=True
    )

# 4. Logika Tombol Proses
if st.button("Proses Dokumen"):
    # Validasi Input
    if not api_key:
        st.error("⚠️ Harap masukkan API Key di sidebar!")
    elif not uploaded_template:
        st.error("⚠️ Harap upload Template Word!")
    elif not uploaded_files:
        st.error("⚠️ Harap upload minimal 1 dokumen (Gambar atau PDF)!")
    else:
        with st.spinner('Sedang membaca dokumen (termasuk PDF)...'):
            try:
                # A. Siapkan Model AI
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # B. Siapkan Dokumen untuk dikirim ke AI
                input_parts = []
                for file in uploaded_files:
                    # Membaca data file dalam bentuk bytes
                    file_bytes = file.getvalue()
                    
                    # Menambahkan ke list dengan mime_type yang sesuai (image/jpeg atau application/pdf)
                    input_parts.append({
                        "mime_type": file.type,
                        "data": file_bytes
                    })

                # C. Prompt Instruksi (Perintah untuk AI)
                prompt = """
                Anda adalah asisten legal profesional.
                Tugas: Ekstrak data dari dokumen-dokumen terlampir (bisa berupa gambar atau PDF).
                Keluarkan output HANYA dalam format JSON valid. Jangan pakai markdown ```json.
                
                Gunakan keys persis seperti ini (kosongkan string jika tidak ada/tidak terbaca):
                {
                  "nama_penjual": "", "nik_penjual": "", "tempat_lahir_penjual": "", "tanggal_lahir_penjual": "", "pekerjaan_penjual": "", "alamat_penjual": "",
                  "nama_pembeli": "", "nik_pembeli": "", "pekerjaan_pembeli": "", "alamat_pembeli": "",
                  "no_sertifikat": "", "jenis_hak": "", "luas_tanah": "", "kelurahan": "", "kecamatan": "", "kabupaten": "",
                  "nop_pbb": "", "njop_total": "", "tahun_pajak": ""
                }
                
                Aturan Format:
                1. Tanggal format DD-MM-YYYY. 
                2. Angka (Luas/NJOP) ambil angkanya saja tanpa 'Rp' atau titik/koma pemisah ribuan.
                3. Jika dokumen buram, tulis "TIDAK TERBACA".
                """
                
                # D. Kirim ke Gemini (Prompt + File)
                request_content = [prompt] + input_parts
                response = model.generate_content(request_content)
                
                # E. Bersihkan hasil JSON
                text_result = response.text.replace("```json", "").replace("```", "").strip()
                data_json = json.loads(text_result)
                
                # Tampilkan Preview Data
                st.success("✅ Ekstraksi Berhasil!")
                st.write("Preview Data yang akan dimasukkan:")
                st.json(data_json)
                
                # F. Masukkan ke Word (Render Template)
                doc = DocxTemplate(uploaded_template)
                doc.render(data_json)
                
                # G. Siapkan Download
                bio = io.BytesIO()
                doc.save(bio)
                
                st.download_button(
                    label="⬇️ Download Draf Akta (.docx)",
                    data=bio.getvalue(),
                    file_name="Hasil_Draf_Akta.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            except Exception as e:
                st.error(f"Terjadi kesalahan teknis: {e}")
                st.warning("Tips: Pastikan PDF tidak dipassword dan API Key benar.")
