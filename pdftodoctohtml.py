from flask import Flask, request, jsonify
import io
import requests
import mammoth
from pdfservices_sdk.credentials import Credentials
from pdfservices_sdk.execution_context import ExecutionContext
from pdfservices_sdk.io.file_ref import FileRef
from pdfservices_sdk.pdfops.export_pdf_operation import ExportPDFOperation
from pdfservices_sdk.pdfops.options.export_pdf.export_pdf_options import ExportPDFOptions, ExportPDFTargetFormat

app = Flask(__name__)

# Convert PDF URL to HTML directly
@app.route("/convert", methods=["POST"])
def convert_pdf_url_to_html():
    data = request.get_json()
    pdf_url = data.get("url")

    if not pdf_url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    try:
        # Step 1: Stream PDF from URL
        pdf_response = requests.get(pdf_url, stream=True)
        if pdf_response.status_code != 200:
            return jsonify({"error": f"Failed to fetch PDF from URL: {pdf_url}"}), 400

        pdf_stream = io.BytesIO(pdf_response.content)

        # Step 2: Convert PDF stream to DOCX using Adobe API
        credentials = Credentials.service_account_credentials_builder() \
            .from_file("pdfservices-api-credentials.json") \
            .build()
        execution_context = ExecutionContext.create(credentials)

        export_pdf = ExportPDFOperation.create_new(
            ExportPDFOptions.builder().with_export_format(ExportPDFTargetFormat.DOCX).build()
        )

        input_pdf = FileRef.create_from_stream(pdf_stream, ExportPDFTargetFormat.PDF)
        export_pdf.set_input(input_pdf)

        result = export_pdf.execute(execution_context)

        # Step 3: Convert result DOCX to HTML
        docx_stream = io.BytesIO()
        result.save_as_stream(docx_stream)
        docx_stream.seek(0)

        html_result = mammoth.convert_to_html(docx_stream).value

        return html_result

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)