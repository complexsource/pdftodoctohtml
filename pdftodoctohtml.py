from flask import Flask, request, jsonify
from pdf2docx import Converter
import mammoth
import os
import tempfile
from docx import Document

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_all_pages():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded with key "pdf"'}), 400

    pdf_file = request.files['pdf']

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
            pdf_file.save(tmp_pdf.name)

            # Count pages first
            from fitz import open as fitz_open
            doc = fitz_open(tmp_pdf.name)
            num_pages = doc.page_count
            doc.close()

            # Prepare merged DOCX
            merged_docx = Document()
            for i in range(num_pages):
                with tempfile.NamedTemporaryFile(suffix=".docx") as single_docx:
                    converter = Converter(tmp_pdf.name)
                    converter.convert(single_docx.name, pages=[i])
                    converter.close()

                    sub_doc = Document(single_docx.name)
                    for element in sub_doc.element.body:
                        merged_docx.element.body.append(element)

            # Save merged DOCX to memory temp
            with tempfile.NamedTemporaryFile(suffix=".docx") as final_docx:
                merged_docx.save(final_docx.name)

                # Convert to HTML
                with open(final_docx.name, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value

        return jsonify({
            "success": True,
            "pages": num_pages,
            "html": html_content
        })

    except Exception as e:
        return jsonify({"error": f"Conversion failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)