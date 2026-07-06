import boto3
import os
import tempfile

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

s3 = boto3.client("s3")


def create_watermark(text, output_path):
    c = canvas.Canvas(output_path)

    c.setFont("Helvetica", 40)

    # Light gray watermark
    c.setFillColor(Color(0.7, 0.7, 0.7, alpha=0.3))

    c.saveState()

    c.translate(300, 400)
    c.rotate(45)

    c.drawCentredString(0, 0, text)

    c.restoreState()

    c.save()


def lambda_handler(event, context):

    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    print(bucket)
    print(key)

    input_pdf = tempfile.NamedTemporaryFile(delete=False).name
    watermark_pdf = tempfile.NamedTemporaryFile(delete=False).name
    output_pdf = tempfile.NamedTemporaryFile(delete=False).name

    # Download uploaded PDF
    s3.download_file(bucket, key, input_pdf)

    # Create watermark
    create_watermark("DocArmor", watermark_pdf)

    reader = PdfReader(input_pdf)
    watermark = PdfReader(watermark_pdf)

    writer = PdfWriter()

    wm_page = watermark.pages[0]

    for page in reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

    output_key = key.replace("uploads/", "processed/")

    s3.upload_file(
        output_pdf,
        bucket,
        output_key
    )

    return {
        "statusCode": 200,
        "body": "Watermark Applied"
    }