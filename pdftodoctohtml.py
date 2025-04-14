from flask import Flask, request, jsonify
from pdf2docx import Converter
import mammoth
import os
import tempfile
from docx import Document
import fitz  # PyMuPDF for counting pages

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_html_response():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file part with name "pdf"'}), 400

    pdf_file = request.files['pdf']
    if pdf_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Step 1: Save uploaded PDF to a temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
        pdf_file.save(tmp_pdf.name)

        try:
            # Step 2: Count number of pages
            doc = fitz.open(tmp_pdf.name)
            total_pages = min(doc.page_count, 10)
            doc.close()
        except Exception as e:
            return jsonify({'error': f'Failed to count pages: {str(e)}'}), 500

        try:
            # Step 3: Create a combined Word doc
            merged_docx = Document()

            for i in range(total_pages):
                with tempfile.NamedTemporaryFile(suffix=".docx") as single_docx:
                    converter = Converter(tmp_pdf.name)
                    converter.convert(single_docx.name, pages=[i])
                    converter.close()

                    sub_doc = Document(single_docx.name)
                    for element in sub_doc.element.body:
                        merged_docx.element.body.append(element)

            # Step 4: Convert combined docx to HTML
            with tempfile.NamedTemporaryFile(suffix=".docx") as final_docx:
                merged_docx.save(final_docx.name)

                with open(final_docx.name, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value

        except Exception as e:
            return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

    return jsonify({
        "success": True,
        "pages_converted": total_pages,
        "html": html_content
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)