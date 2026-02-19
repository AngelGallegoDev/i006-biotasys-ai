import os
import random
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

def generate_realistic_report(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='SubTitle', fontSize=14, spaceAfter=10, textColor=colors.HexColor("#3b82f6"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='MainTitle', fontSize=22, spaceAfter=20, textColor=colors.black, fontName="Helvetica-Bold", alignment=1))
    
    elements = []

    # 1. Header
    elements.append(Paragraph("INFORME DE MICROBIOTA COMPLETO", styles['MainTitle']))
    
    patient_data = [
        ["Paciente:", f"MOCK_{random.randint(1000, 9999)}"],
        ["ID Documento:", f"DOC-{datetime.now().year}-{random.randint(100, 999)}"],
        ["Fecha de Análisis:", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Laboratorio:", "Biotasys Research Lab - Central B2B"],
    ]
    
    t_header = Table(patient_data, colWidths=[1.5*inch, 4*inch])
    t_header.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,-1), colors.darkgrey),
    ]))
    elements.append(t_header)
    elements.append(Spacer(1, 0.2*inch))

    # 1.1 Gestión de Muestra
    elements.append(Paragraph("Gestión de la Muestra", ParagraphStyle(name='MiniTitle', fontSize=10, fontName="Helvetica-Bold")))
    sample_data = [
        ["Método de Recolección:", "Hisopado rectal / Materia Fecal"],
        ["Condiciones de Transporte:", "Refrigerado (4°C)"],
        ["Estado al recibir:", "Óptimo / Sellado"],
    ]
    t_sample = Table(sample_data, colWidths=[2.5*inch, 3*inch])
    t_sample.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), colors.grey),
    ]))
    elements.append(t_sample)
    elements.append(Spacer(1, 0.3*inch))

    # 2. Resumen de Diversidad
    elements.append(Paragraph("Resumen de Diversidad Microbiana", styles['SubTitle']))
    shannon = round(random.uniform(2.5, 4.5), 2)
    simpson = round(random.uniform(0.7, 0.95), 2)
    otus = random.randint(150, 450)
    
    div_text = f"El análisis muestra un índice de <b>Shannon de {shannon}</b> y un índice de <b>Simpson de {simpson}</b>, indicando una diversidad de nivel {'alto' if shannon > 3.8 else 'moderado'}. Se han detectado {otus} OTUs significativos."
    elements.append(Paragraph(div_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # 3. Composición Taxonómica (Table)
    elements.append(Paragraph("Abundancia Taxonómica (Principales Filos)", styles['SubTitle']))
    
    taxa_data = [["Rango", "Nombre Científico", "Abundancia %", "Rango Ref."]]
    phyla = [
        ["Filo", "Firmicutes", f"{round(random.uniform(40, 65), 2)}%", "40-70%"],
        ["Filo", "Bacteroidetes", f"{round(random.uniform(20, 40), 2)}%", "15-40%"],
        ["Filo", "Actinobacteria", f"{round(random.uniform(2, 10), 2)}%", "1-12%"],
        ["Filo", "Proteobacteria", f"{round(random.uniform(0.5, 5), 2)}%", "0.1-5%"],
        ["Filo", "Verrucomicrobia", f"{round(random.uniform(0.1, 3), 2)}%", "0-4%"],
        ["Filo", "Otros", f"{round(random.uniform(1, 5), 2)}%", "< 5%"],
    ]
    taxa_data.extend(phyla)
    
    t_taxa = Table(taxa_data, colWidths=[1*inch, 2*inch, 1.25*inch, 1.25*inch])
    t_taxa.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3b82f6")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.white])
    ]))
    elements.append(t_taxa)
    elements.append(Spacer(1, 0.3*inch))

    # 4. Marcadores Funcionales
    elements.append(Paragraph("Marcadores Metabólicos y Funcionales", styles['SubTitle']))
    func_data = [
        ["Producción de Butirato", "Óptima" if random.random() > 0.3 else "Reducida"],
        ["Metabolismo de GABA", "Normal"],
        ["Producción de Lipopolisacáridos (LPS)", "Baja (Deseable)"],
        ["Capacidad de degradación de moco", "Balanceada"],
    ]
    elements.append(Paragraph("<b>Inferencia Funcional (PICRUSt2):</b>", styles['Normal']))
    picrust_data = [
        ["Metabolismo de Carbohidratos:", "Nivel Alto"],
        ["Metabolismo de Lípidos:", "Nivel Normal"],
        ["Síntesis de Vitaminas (Grupo B):", "Nivel Reducido"],
    ]
    for p_label, p_val in picrust_data:
        elements.append(Paragraph(f"• {p_label} <font color='#3b82f6'>{p_val}</font>", styles['Normal']))
    
    elements.append(Spacer(1, 0.1*inch))
    
    for fiber, status in func_data:
        color = "#10b981" if status in ["Óptima", "Normal", "Baja (Deseable)", "Balanceada"] else "#f59e0b"
        p_text = f"• <b>{fiber}:</b> <font color='{color}'>{status}</font>"
        elements.append(Paragraph(p_text, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))

    # 5. Notas Clínicas (Texto libre para que el Extractor lo lea)
    elements.append(Paragraph("Observaciones del Laboratorio", styles['SubTitle']))
    obs_text = """Se observa una ligera disminución en la abundancia de bacterias productoras de ácidos grasos de cadena corta (AGCC). El ratio Firmicutes/Bacteroidetes se encuentra dentro de los parámetros normales, aunque con tendencia a la adiposidad. No se detectan sobrecrecimientos significativos de patógenos oportunistas como C. difficile o Candida spp. en esta muestra."""
    elements.append(Paragraph(obs_text, styles['Normal']))

    # Final Footnote
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Este documento es un mock generado automáticamente para pruebas del Biotasys Engine Sandbox.", ParagraphStyle(name='Foot', fontSize=8, textColor=colors.grey, alignment=1)))

    doc.build(elements)
    print(f"✅ Reporte generado en: {output_path}")

if __name__ == "__main__":
    output_dir = "tests/mock_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(3):
        path = os.path.join(output_dir, f"mock_report_{i+1}.pdf")
        generate_realistic_report(path)
