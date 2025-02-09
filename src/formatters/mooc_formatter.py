import json
from typing import List, Dict, Any
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.units import inch

class MOOCFormatter:
    """Class to format MOOC storyboard results into a PDF document."""
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the MOOCFormatter.
        
        Args:
            output_dir (str): Directory where the PDF will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create custom styles
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='CellStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=10
        ))

    def sanitize_content(self, content: str) -> str:
        """
        Sanitize content to be compatible with ReportLab's paragraph parser.
        
        Args:
            content (str): Raw content to sanitize
            
        Returns:
            str: Sanitized content
        """
        # Replace markdown-style links with simple text
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)
        
        # Replace HTML links with simple text
        content = re.sub(r'<a.*?>(.*?)</a>', r'\1', content)
        
        # Remove image tags
        content = re.sub(r'!\[.*?\]\(.*?\)', '[Image]', content)
        content = re.sub(r'<img.*?/>', '[Image]', content)
        
        # Convert markdown bullet points to simple bullet points
        content = content.replace('* ', '• ')
        
        # Clean up any remaining HTML tags except for basic formatting
        allowed_tags = ['b', 'i', 'u', 'br']
        content = re.sub(r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]*>', '', content)
        
        return content
        
    def format_slide_content(self, slide_number: int, title: str, content: str) -> str:
        """
        Format the slide content with proper structure.
        
        Args:
            slide_number (int): Number of the slide
            title (str): Slide title
            content (str): Slide content
            
        Returns:
            str: Formatted slide content
        """
        # Sanitize the content while preserving basic formatting
        sanitized_content = self.sanitize_content(content)
        
        # Format with slide number, title, and sanitized content
        return f"<b>Slide {slide_number}:</b> {title}<br/><br/>{sanitized_content}"
        
    def create_pdf(self, json_data: List[Dict[str, Any]], output_filename: str) -> str:
        """
        Create a PDF document from the MOOC storyboard results.
        
        Args:
            json_data (List[Dict[str, Any]]): List of slide results
            output_filename (str): Name of the output PDF file
            
        Returns:
            str: Path to the generated PDF file
        """
        # Prepare the output path
        output_path = self.output_dir / f"{output_filename}.pdf"
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Prepare the table data
        table_data = [["Slide Content", "Instructor Dialogue"]]  # Header row
        
        # Add content rows
        for idx, item in enumerate(json_data, 1):
            result = item["result"]
            
            # Format and sanitize slide content
            formatted_content = self.format_slide_content(
                idx,
                result["title"],
                result["content"]
            )
            
            # Sanitize dialogue content
            sanitized_dialogue = self.sanitize_content(result["dialogue"])
            
            content_cell = Paragraph(formatted_content, self.styles["CellStyle"])
            dialogue_cell = Paragraph(sanitized_dialogue, self.styles["CellStyle"])
            table_data.append([content_cell, dialogue_cell])
        
        # Create the table
        table = Table(
            table_data,
            colWidths=[3.25*inch, 3.25*inch],
            repeatRows=1  # Repeat header row on each page
        )
        
        # Style the table
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            # Table grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Cell alignment
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Alternate row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            # Cell padding
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        # Build the PDF
        doc.build([table])
        
        return str(output_path)
        
    def format_results(self, input_file: str) -> str:
        """
        Format results from a JSON file into a PDF.
        
        Args:
            input_file (str): Path to the input JSON file
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Read the input JSON file
            with open(input_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            # Create the PDF
            output_filename = Path(input_file).stem.replace('_results', '_pdf')
            pdf_path = self.create_pdf(json_data, output_filename)
            
            print(f"PDF successfully generated at: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Error formatting results: {e}")
            raise