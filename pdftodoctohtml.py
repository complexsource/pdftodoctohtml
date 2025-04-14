from flask import Flask, request, jsonify
from pdf2docx import Converter
import mammoth
import tempfile
from docx import Document
import fitz  # PyMuPDF to count pages
import requests

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_html():
    pdf_source = None
    temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)

    try:
        # CASE 1: Uploaded via form-data
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            pdf_file.save(temp_pdf.name)
            pdf_source = 'upload'

        # CASE 2: Provided via URL
        elif request.is_json and 'url' in request.json:
            url = request.json.get('url')
            response = requests.get(url)
            response.raise_for_status()
            temp_pdf.write(response.content)
            temp_pdf.flush()
            pdf_source = 'url'
        else:
            return jsonify({'error': 'Provide either a file or a url'}), 400

        # Step 2: Count pages (max 10)
        doc = fitz.open(temp_pdf.name)
        total_pages = min(doc.page_count, 10)
        doc.close()

        # Step 3: Convert each page individually and merge
        merged_docx = Document()

        for i in range(total_pages):
            with tempfile.NamedTemporaryFile(suffix=".docx") as single_docx:
                converter = Converter(temp_pdf.name)
                converter.convert(single_docx.name, pages=[i])
                converter.close()

                sub_doc = Document(single_docx.name)
                for element in sub_doc.element.body:
                    merged_docx.element.body.append(element)

        # Step 4: Convert final merged DOCX to HTML
        with tempfile.NamedTemporaryFile(suffix=".docx") as final_docx:
            merged_docx.save(final_docx.name)
            with open(final_docx.name, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html_content = result.value

        return jsonify({
            "success": True,
            "source": pdf_source,
            "pages_converted": total_pages,
            "html": html_content
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to fetch PDF from URL: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
    finally:
        temp_pdf.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)