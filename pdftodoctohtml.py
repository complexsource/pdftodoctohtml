from flask import Flask, request, jsonify
from pdf2docx import Converter
import mammoth
import tempfile
import fitz  # PyMuPDF to count pages
import requests

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_html():
    pdf_source = None

    try:
        # CASE 1: Uploaded via form-data
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            pdf_bytes = pdf_file.read()
            pdf_source = 'upload'

        # CASE 2: Provided via URL
        elif request.is_json and 'url' in request.json:
            url = request.json.get('url')
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            pdf_bytes = response.content
            pdf_source = 'url'
        else:
            return jsonify({'error': 'Provide either a PDF file or a URL'}), 400

        # Save PDF to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp_pdf:
            tmp_pdf.write(pdf_bytes)
            tmp_pdf.flush()

            # Count number of pages (max 10)
            doc = fitz.open(tmp_pdf.name)
            total_pages = min(doc.page_count, 10)
            doc.close()

            # Convert up to 10 pages in one go (avoids merge errors)
            with tempfile.NamedTemporaryFile(suffix=".docx") as tmp_docx:
                converter = Converter(tmp_pdf.name)
                converter.convert(tmp_docx.name, start=0, end=total_pages - 1)
                converter.close()

                # Convert the DOCX to HTML using Mammoth
                with open(tmp_docx.name, "rb") as docx_file:
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)