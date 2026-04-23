# PDF / DOCX / test reusme parsing
import pypdf
from docx import Document
import io
def parse_resume(file):
    # Determine file type and parse accordingly
    if isinstance(file, str):
        # if called from test function
        filename = file
    else:
        # if calle from streamlit file uploader 
        filename = file.name
    
    # route to the correct parsing method based on file extension
    if filename.endswith('.pdf'): # if file is a PDF
        return parse_pdf(file)
    elif filename.endswith('.docx'): # if file is a DOCX    
        return parse_docx(file)
    else: # if neither, then return error message
        return "Unsupported file format. Please upload a PDF or DOCX file."
    
    
    
def parse_pdf(file):
    try:
        reader = pypdf.PdfReader(file)
        text = " ".join(page.extract_text() for page in reader.pages)
        print("File parsed successfully")
        return text
    except Exception as e:
        return f"Error parsing PDF: {e}"


def parse_docx(file):
    try:
        if not isinstance(file, str):
            file = io.BytesIO(file.read())
        doc = Document(file)
        text = " ".join(para.text for para in doc.paragraphs)
        print("File parsed successfully")
        return text
    except Exception as e:
        return f"Error parsing DOCX: {e}"