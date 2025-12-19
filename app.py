import streamlit as st
import google.generativeai as genai
from docxtpl import DocxTemplate
from PIL import Image
import json
import io

# Konfigurasi Halaman
st.set_page_config(page_title="AI Notaris MVP", page_icon="⚖️")

st.title("⚖️ AI Notaris - Auto Drafting")
st.markdown("Upload dokumen, biarkan AI mengisi draf Akta Anda.")

# Sidebar untuk API Key
with st.sidebar:
    st.header("Konfigurasi")
    api_key = st.text_input("Masukkan Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    st.info("Pastikan Anda punya Template Word yang sesuai.")

# Upload File
col1, col2 = st.columns(2)
with col1:
    uploaded_template = st.file_uploader("1. Upload Template Word (.docx)", type="docx")
with col2:
    uploaded_images = st.file_uploader("2. Upload Gambar (KTP/Sertifikat/PBB)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Tombol Proses
if st.button("Proses Dokumen"):
    if not api_key:
        st.error("⚠️ Harap masukkan API Key di sidebar!")
    elif not uploaded_template:
        st.error("⚠️ Harap upload Template Word!")
    elif not uploaded_images:
        st.error("⚠️ Harap upload minimal 1 gambar!")
    else:
        with st.spinner('Sedang membaca dokumen dengan mata AI...'):
            try:
                # 1. Siapkan Model
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 2. Siapkan Gambar untuk dikirim
                image_parts = []
                for img_file in uploaded_images:
                    image_bytes = img_file.getvalue()
                    image_parts.append({
                        "mime_type": img_file.type,
                        "data": image_bytes
                    })

                # 3. Prompt Instruksi
                prompt = """
                Ekstrak data dari gambar-gambar legal Indonesia terlampir.
                Keluarkan output HANYA dalam format JSON valid. Jangan pakai markdown.
                
                Gunakan keys persis seperti ini (kosongkan string jika tidak ada):
                {
                  "nama_penjual": "", "nik_penjual": "", "tempat_lahir_penjual": "", "tanggal_lahir_penjual": "", "pekerjaan_penjual": "", "alamat_penjual": "",
                  "nama_pembeli": "", "nik_pembeli": "", "pekerjaan_pembeli": "", "alamat_pembeli": "",
                  "no_sertifikat": "", "jenis_hak": "", "luas_tanah": "", "kelurahan": "", "kecamatan": "", "kabupaten": "",
                  "nop_pbb": "", "njop_total": "", "tahun_pajak": ""
                }
                
                Pastikan tanggal format DD-MM-YYYY. Angka tanpa Rp atau titik.
                """
                
                # 4. Kirim ke Gemini
                request_content = [prompt] + image_parts
                response = model.generate_content(request_content)
                
                # 5. Bersihkan hasil JSON (kadang AI kasih ```json di awal)
                text_result = response.text.replace("```json", "").replace("```", "").strip()
                data_json = json.loads(text_result)
                
                st.success("Data berhasil diekstrak!")
                st.json(data_json) # Tampilkan di layar untuk dicek user
                
                # 6. Masukkan ke Word
                doc = DocxTemplate(uploaded_template)
                doc.render(data_json)
                
                # 7. Siapkan Download
                bio = io.BytesIO()
                doc.save(bio)
                
                st.download_button(
                    label="⬇️ Download Draf Akta Jadi (.docx)",
                    data=bio.getvalue(),
                    file_name="Draf_Akta_AI.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
