import io
import markdown
import docx

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class DocumentService:
    @staticmethod
    def extract_text(filename: str, content: bytes) -> str:
        """Extracts text from various file formats."""
        ext = filename.split('.')[-1].lower()
        if ext == 'pdf':
            if not pdfplumber:
                return "PDF extraction is not available. Please install pdfplumber."
            text = ""
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text
        elif ext in ['doc', 'docx']:
            doc = docx.Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs])
        elif ext in ['md', 'markdown']:
            # We can just return the raw markdown for the model to read
            return content.decode('utf-8', errors='ignore')
        elif ext == 'txt':
            return content.decode('utf-8', errors='ignore')
        else:
            return "Unsupported file format."

document_service = DocumentService()
