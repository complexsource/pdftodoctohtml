from flask import Flask, request, jsonify
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
        'docx_file': f'/doc/{filename_base}.docx',
        'html_file': f'/html/{filename_base}.html'
    })

# Serve files from folders (for testing/download)
@app.route('/doc/<filename>')
def get_docx(filename):
    return app.send_static_file(os.path.join(DOC_FOLDER, filename))

@app.route('/html/<filename>')
def get_html(filename):
    return app.send_static_file(os.path.join(HTML_FOLDER, filename))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)