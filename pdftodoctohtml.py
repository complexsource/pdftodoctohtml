from flask import Flask, request, jsonify
from pdf2docx import Converter
import mammoth
import os
import tempfile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_html_response():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file part with name "pdf"'}), 400

    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Step 1: Save uploaded PDF to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
        pdf_file.save(tmp_pdf.name)

        # Step 2: Convert to DOCX into a temp file
        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp_docx:
            try:
                converter = Converter(tmp_pdf.name)
                converter.convert(tmp_docx.name, start=0, end=None)
                converter.close()
            except Exception as e:
                return jsonify({'error': f'PDF to DOCX conversion failed: {str(e)}'}), 500

            # Step 3: Convert DOCX to HTML (in memory)
            try:
                with open(tmp_docx.name, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value
            except Exception as e:
                return jsonify({'error': f'DOCX to HTML conversion failed: {str(e)}'}), 500

    # Step 4: Return HTML content in JSON response
    return jsonify({
        "success": True,
        "html": html_content
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)