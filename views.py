import boto3
import requests
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from .models import Student
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_student(request):
    student_id = request.GET.get('student_id')
    display_option = request.GET.get('display_option')

    if student_id:
        try:
            student = Student.objects.get(AdmissionionID=student_id)

            if display_option == 'pdf_horizontal' or display_option == 'pdf_vertical':
                # Generate and return PDF file
                doc = SimpleDocTemplate(tempfile.NamedTemporaryFile(suffix='.pdf').name, pagesize=letter)

                elements = []

                # Define custom styles for the PDF content
                styles = getSampleStyleSheet()
                header_style = styles['Heading1']
                name_style = styles['Heading2']
                field_style = styles['Normal']

                # Add content to the PDF
                elements.append(Paragraph('Student Details', header_style))
                elements.append(Spacer(1, 20))
                elements.append(Paragraph(f'Name: {student.Name}', name_style))
                elements.append(Paragraph(f'Date of Birth: {student.DataOfBirth}', field_style))
                elements.append(Paragraph(f'Gender: {student.Gender}', field_style))
                elements.append(Paragraph(f'Address: {student.Address}', field_style))
                elements.append(Paragraph(f'Admission Date: {student.AdmissionDate}', field_style))

                if display_option == 'pdf_horizontal':
                    doc.pagesize = landscape(letter)

                doc.build(elements)

                # Upload the PDF file to S3
                s3 = boto3.client('s3',
                                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                                  verify=True)  # Enable SSL certificate verification

                bucket_name = 'aitech11'  # Replace with your S3 bucket name
                s3_filepath = f"problem11/all_pdf's/student_{student_id}.pdf"

                with open(doc.filename, 'rb') as file_obj:
                    s3.upload_fileobj(file_obj, bucket_name, s3_filepath)

                # Generate the S3 URL for the uploaded file
                s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_filepath}"

                # Redirect to the S3 URL or display it as a download link
                return HttpResponse(f"PDF uploaded successfully. <a href='{s3_url}'>Download PDF</a>")

            elif display_option == 'records_between':
                # Fetch and display records between dates
                start_date = request.GET.get('start_date')
                end_date = request.GET.get('end_date')

                # Query student records between the selected dates
                records = Student.objects.filter(AdmissionDate__range=[start_date, end_date])

                # Prepare the data for display
                data = [
                    ['Name', 'Date of Birth', 'Gender', 'Address', 'Admission Date'],
                ]

                for record in records:
                    data.append([
                        record.Name,
                        str(record.DataOfBirth),
                        record.Gender,
                        record.Address,
                        str(record.AdmissionDate),
                    ])

                # Create a table with the data
                table = Table(data)

                # Render the student details on a new page
                return render(request, 'problem11/student_details.html', {'student': student, 'table': table})

        except Student.DoesNotExist:
            return HttpResponse('Student not found')

    return render(request, 'problem11/get_student.html')
