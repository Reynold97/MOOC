import json
from typing import List, Dict, Any
from pathlib import Path
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
        for item in json_data:
            result = item["result"]
            content_cell = Paragraph(result["content"], self.styles["CellStyle"])
            dialogue_cell = Paragraph(result["dialogue"], self.styles["CellStyle"])
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