import streamlit as st
from PIL import Image
from google_generativeai import GeminiAPI
from docx import Document
from docxtpl import DocxTemplate
import json

# Function to process documents
def process_documents(api_key, template_file, images):
    gemini = GeminiAPI(api_key)
    
    # Upload images to Gemini API
    results = []
    for image in images:
        response = gemini.process_image(image, model="gemini-1.5-flash")
        results.append(response)
    
    # Parse JSON results
    data = {}
    for i, key in enumerate([
       "nama_penjual", "nik_penjual", "tempat_lahir_penjual", "tanggal_lahir_penjual", "pekerjaan_penjual", "alamat_penjual",
       "nama_pembeli", "nik_pembeli", "pekerjaan_pembeli", "alamat_pembeli",
       "no_sertifikat", "jenis_hak", "luas_tanah", "kelurahan", "kecamatan", "kabupaten",
       "nop_pbb", "njop_total", "tahun_pajak"
    ]):
        data[key] = results[i]
    
    # Load template docx and render data
    doc = DocxTemplate(template_file)
    doc.render(data)
    
    return doc

# Sidebar for API Key input
api_key = st.sidebar.text_input("Enter Gemini API Key", type='password')

# Main content
st.title("Legal Tech Document Processor")
template_file = st.file_uploader("Upload Template Word File (.docx)", type=['docx'])

images = []
for i in range(4):
    image = st.file_uploader(f"Upload Image {i+1}", type=['png', 'jpg', 'pdf'])
    if image:
        images.append(Image.open(image))

if st.button("Process Documents"):
    if not api_key:
        st.error("Please enter your Gemini API Key.")
    elif not template_file:
        st.error("Please upload the Template Word File.")
    elif len(images) != 4:
        st.error("Please upload all 4 images.")
    else:
        try:
            doc = process_documents(api_key, template_file, images)
            st.download_button("Download Processed Document", doc.save("result.docx"), file_name="result.docx", mime="application/octet-stream")
        except json.JSONDecodeError:
            st.error("Error: Invalid JSON data from Gemini API.")
