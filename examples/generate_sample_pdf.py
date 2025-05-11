#!/usr/bin/env python3
"""
Generate a sample PDF for testing the Searchable PDF Library.
This script creates a simple PDF with text, tables, and form fields.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def main():
    """Generate a sample PDF."""
    # Create output directory
    output_dir = Path("tests/test_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create PDF
    pdf_path = output_dir / "sample.pdf"
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    
    # Create styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Create content
    content = []
    
    # Title
    content.append(Paragraph("Sample PDF Document", title_style))
    content.append(Spacer(1, 12))
    
    # Introduction
    content.append(Paragraph("Introduction", heading_style))
    content.append(Paragraph(
        "This is a sample PDF document generated for testing the Searchable PDF Library. "
        "It contains text, tables, and other elements that can be extracted and analyzed.",
        normal_style
    ))
    content.append(Spacer(1, 12))
    
    # Sample text
    content.append(Paragraph("Sample Text", heading_style))
    content.append(Paragraph(
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec a diam lectus. "
        "Sed sit amet ipsum mauris. Maecenas congue ligula ac quam viverra nec consectetur ante hendrerit. "
        "Donec et mollis dolor. Praesent et diam eget libero egestas mattis sit amet vitae augue.",
        normal_style
    ))
    content.append(Spacer(1, 12))
    
    # Sample table
    content.append(Paragraph("Sample Table", heading_style))
    data = [
        ['Name', 'Age', 'City', 'Occupation'],
        ['John Doe', '32', 'New York', 'Engineer'],
        ['Jane Smith', '28', 'San Francisco', 'Designer'],
        ['Bob Johnson', '45', 'Chicago', 'Manager'],
        ['Alice Williams', '37', 'Boston', 'Doctor']
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(table)
    content.append(Spacer(1, 12))
    
    # Sample list
    content.append(Paragraph("Sample List", heading_style))
    content.append(Paragraph("Here is a list of items:", normal_style))
    for i in range(1, 6):
        content.append(Paragraph(f"• Item {i}: This is item number {i} in the list.", normal_style))
    content.append(Spacer(1, 12))
    
    # Sample entities
    content.append(Paragraph("Sample Entities", heading_style))
    content.append(Paragraph(
        "This section contains named entities that can be extracted: "
        "John Smith works at Microsoft Corporation in Seattle, Washington. "
        "He previously worked at Apple Inc. from January 2015 to December 2020. "
        "He graduated from Stanford University with a degree in Computer Science.",
        normal_style
    ))
    content.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(content)
    
    print(f"Sample PDF created at: {pdf_path}")
    
    # Create table sample
    table_pdf_path = output_dir / "table_sample.pdf"
    doc = SimpleDocTemplate(str(table_pdf_path), pagesize=letter)
    
    content = []
    content.append(Paragraph("PDF with Tables", title_style))
    content.append(Spacer(1, 12))
    
    # Table 1
    content.append(Paragraph("Table 1: Employee Information", heading_style))
    data = [
        ['ID', 'Name', 'Department', 'Salary', 'Start Date'],
        ['001', 'John Doe', 'Engineering', '$85,000', '2018-05-15'],
        ['002', 'Jane Smith', 'Design', '$75,000', '2019-02-10'],
        ['003', 'Bob Johnson', 'Marketing', '$65,000', '2020-01-05'],
        ['004', 'Alice Williams', 'HR', '$70,000', '2017-11-20'],
        ['005', 'Charlie Brown', 'Engineering', '$90,000', '2016-08-12']
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(table)
    content.append(Spacer(1, 24))
    
    # Table 2
    content.append(Paragraph("Table 2: Product Inventory", heading_style))
    data = [
        ['Product ID', 'Name', 'Category', 'Price', 'Stock'],
        ['P001', 'Laptop', 'Electronics', '$1,200', '45'],
        ['P002', 'Desk Chair', 'Furniture', '$250', '30'],
        ['P003', 'Coffee Maker', 'Appliances', '$85', '20'],
        ['P004', 'Headphones', 'Electronics', '$150', '100'],
        ['P005', 'Desk Lamp', 'Furniture', '$45', '50']
    ]
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    print(f"Table sample PDF created at: {table_pdf_path}")

if __name__ == "__main__":
    main()
