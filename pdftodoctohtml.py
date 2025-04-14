from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pdf2docx import Converter
import mammoth
import os

app = Flask(__name__)

# Folder paths
UPLOAD_FOLDER = 'uploads'
DOC_FOLDER = 'doc'
HTML_FOLDER = 'html'

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOC_FOLDER, exist_ok=True)
os.makedirs(HTML_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file part with name "pdf"'}), 400

    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Secure and set paths
    filename_base = os.path.splitext(secure_filename(pdf_file.filename))[0].replace(' ', '-')
    pdf_path = os.path.join(UPLOAD_FOLDER, f'{filename_base}.pdf')
    docx_path = os.path.join(DOC_FOLDER, f'{filename_base}.docx')
    html_path = os.path.join(HTML_FOLDER, f'{filename_base}.html')

    # Save PDF
    pdf_file.save(pdf_path)

    # Convert PDF → DOCX
    try:
        converter = Converter(pdf_path)
        converter.convert(docx_path, start=0, end=None)
        converter.close()
    except Exception as e:
        return jsonify({'error': f'Failed to convert PDF to DOCX: {str(e)}'}), 500

    # Convert DOCX → HTML
    try:
        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(result.value)
    except Exception as e:
        return jsonify({'error': f'Failed to convert DOCX to HTML: {str(e)}'}), 500

    return jsonify({
        'success': True,
        'message': 'Files converted successfully',
        'docx_file': f'/doc/{filename_base}.docx',
        'html_file': f'/html/{filename_base}.html',
        'download_info': f'/download/{filename_base}'
    })

@app.route('/download/<filename>', methods=['GET'])
def download_links(filename):
    base_name = os.path.splitext(filename)[0]
    docx_path = os.path.join(DOC_FOLDER, f"{base_name}.docx")
    html_path = os.path.join(HTML_FOLDER, f"{base_name}.html")

    if not os.path.exists(docx_path) or not os.path.exists(html_path):
        return jsonify({"error": "One or both files not found"}), 404

    return jsonify({
        "download_docx": f"/get-docx/{base_name}.docx",
        "download_html": f"/get-html/{base_name}.html"
    })

@app.route('/get-docx/<filename>', methods=['GET'])
def get_docx(filename):
    return send_from_directory(DOC_FOLDER, filename, as_attachment=True)

@app.route('/get-html/<filename>', methods=['GET'])
def get_html(filename):
    return send_from_directory(HTML_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)