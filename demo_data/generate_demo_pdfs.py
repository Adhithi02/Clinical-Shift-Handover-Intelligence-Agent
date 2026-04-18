"""
Generate demo patient PDF reports for the Clinical Shift Handover system.
Uses ReportLab to create structured clinical documents.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def get_styles():
    """Create custom paragraph styles for clinical documents."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ClinicalTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor('#1a365d'),
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor('#2b6cb0'),
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='ClinicalBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='ClinicalNote',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#718096'),
        fontName='Helvetica-Oblique'
    ))
    return styles


def make_vitals_table(data_rows, col_widths=None):
    """Create a styled vitals table."""
    if col_widths is None:
        col_widths = [80, 90, 60, 60, 60]
    
    table = Table(data_rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#a0aec0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def make_info_table(data_rows):
    """Create a key-value patient info table."""
    table = Table(data_rows, colWidths=[120, 350])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
    ]))
    return table


def generate_patient_a(output_path):
    """
    Patient A: Arun Mehta — Triggers Missing Info Agent
    Post-surgery with missing post-op pain score.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           topMargin=30*mm, bottomMargin=20*mm,
                           leftMargin=20*mm, rightMargin=20*mm)
    styles = get_styles()
    story = []

    # Header
    story.append(Paragraph("PATIENT CLINICAL REPORT", styles['ClinicalTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2b6cb0')))
    story.append(Spacer(1, 12))

    # Demographics
    story.append(Paragraph("Patient Demographics", styles['SectionHeader']))
    info_data = [
        ['Patient ID:', 'PAT-A-2024-0471'],
        ['Full Name:', 'Arun Mehta'],
        ['Age:', '58 years'],
        ['Gender:', 'Male'],
        ['Ward:', 'Orthopedic Ward - Bed 14A'],
        ['Admission Date:', '2024-11-14'],
        ['Admitting Doctor:', 'Dr. Sunita Kapoor'],
    ]
    story.append(make_info_table(info_data))
    story.append(Spacer(1, 10))

    # Admission reason
    story.append(Paragraph("Admission Reason", styles['SectionHeader']))
    story.append(Paragraph(
        "Post-surgery recovery: <b>Right total knee replacement (TKR)</b>. "
        "Surgery performed on 2024-11-14 at 14:00 hours under spinal anaesthesia. "
        "Procedure completed without complications. Patient transferred to ward at 16:30.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Vitals
    story.append(Paragraph("Vital Signs", styles['SectionHeader']))
    vitals_data = [
        ['Time', 'Blood Pressure', 'Heart Rate', 'Temp (°C)', 'SpO2 (%)'],
        ['08:00', '124/82', '76', '37.1', '98'],
        ['10:00', '122/80', '74', '37.0', '98'],
        ['12:00', '126/84', '78', '37.1', '97'],
        ['14:00', '120/78', '72', '37.0', '98'],
    ]
    story.append(make_vitals_table(vitals_data))
    story.append(Paragraph(
        "Note: Vitals stable throughout shift. No hemodynamic concerns.",
        styles['ClinicalNote']
    ))
    story.append(Spacer(1, 8))

    # Pain Assessment
    story.append(Paragraph("Pain Assessment", styles['SectionHeader']))
    story.append(Paragraph(
        "Last pain score recorded: <b>4/10 at 09:00</b> (pre-operative assessment).",
        styles['ClinicalBody']
    ))
    story.append(Paragraph(
        "NOTE: Surgery was performed at 14:00. No post-operative pain score has been "
        "documented. Post-op pain assessment is MISSING.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Medications
    story.append(Paragraph("Current Medications", styles['SectionHeader']))
    med_data = [
        ['Medication', 'Dose', 'Route', 'Frequency'],
        ['Paracetamol', '1g', 'Oral', 'QID (6-hourly)'],
        ['Enoxaparin', '40mg', 'Subcutaneous', 'OD (once daily)'],
    ]
    story.append(make_vitals_table(med_data, col_widths=[120, 80, 80, 120]))
    story.append(Spacer(1, 8))

    # Clinical notes
    story.append(Paragraph("Clinical Notes", styles['SectionHeader']))
    story.append(Paragraph(
        "Patient is alert and oriented. Surgical site dressing clean and intact. "
        "Drain output minimal (30ml serous fluid). Physiotherapy initiated — "
        "patient able to sit up with assistance. No signs of DVT. "
        "Continue current management plan.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Report generated: 2024-11-14 at 19:00 | Shift: Day (07:00-19:00) | "
        "Nurse: RN Deepa Krishnan",
        styles['ClinicalNote']
    ))

    doc.build(story)
    print(f"  [OK] Generated: {output_path}")


def generate_patient_b(output_path):
    """
    Patient B: Priya Sharma — Triggers Risk Flag Agent
    Declining BP trend, chest pain with ACS query, missing troponin.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           topMargin=30*mm, bottomMargin=20*mm,
                           leftMargin=20*mm, rightMargin=20*mm)
    styles = get_styles()
    story = []

    # Header
    story.append(Paragraph("PATIENT CLINICAL REPORT", styles['ClinicalTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#c53030')))
    story.append(Spacer(1, 12))

    # Demographics
    story.append(Paragraph("Patient Demographics", styles['SectionHeader']))
    info_data = [
        ['Patient ID:', 'PAT-B-2024-0892'],
        ['Full Name:', 'Priya Sharma'],
        ['Age:', '71 years'],
        ['Gender:', 'Female'],
        ['Ward:', 'Cardiac Care Unit - Bed 3C'],
        ['Admission Date:', '2024-11-14'],
        ['Admitting Doctor:', 'Dr. Rajesh Menon (Cardiology)'],
    ]
    story.append(make_info_table(info_data))
    story.append(Spacer(1, 10))

    # Admission reason
    story.append(Paragraph("Admission Reason", styles['SectionHeader']))
    story.append(Paragraph(
        "Admitted via Emergency Department with <b>acute chest pain — query Acute "
        "Coronary Syndrome (ACS)</b>. Patient reported substernal chest tightness "
        "radiating to left arm, onset at approximately 06:30. Initial ECG showed "
        "non-specific ST changes. Serial troponins ordered.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Vitals — declining BP trend
    story.append(Paragraph("Vital Signs (Serial Monitoring)", styles['SectionHeader']))
    vitals_data = [
        ['Time', 'Blood Pressure', 'Heart Rate', 'Temp (°C)', 'SpO2 (%)'],
        ['08:00', '138/88', '88', '37.0', '96'],
        ['10:00', '131/84', '86', '37.0', '96'],
        ['12:00', '122/79', '90', '37.1', '95'],
        ['14:00', '114/72', '92', '37.0', '94'],
    ]
    story.append(make_vitals_table(vitals_data))
    story.append(Paragraph(
        "ALERT: Blood pressure showing consistent downward trend over 4 consecutive "
        "readings (systolic drop: 138 → 114 mmHg). Heart rate compensatory increase "
        "noted. SpO2 marginal decline.",
        styles['ClinicalNote']
    ))
    story.append(Spacer(1, 8))

    # Investigations
    story.append(Paragraph("Investigations", styles['SectionHeader']))
    story.append(Paragraph(
        "ECG (08:15): Non-specific ST-T wave changes in leads V3-V5. No acute "
        "ST elevation.",
        styles['ClinicalBody']
    ))
    story.append(Paragraph(
        "Troponin I (08:30): 0.04 ng/mL (borderline — normal &lt;0.03)",
        styles['ClinicalBody']
    ))
    story.append(Paragraph(
        "<b>Repeat troponin at 12:00: NOT DOCUMENTED.</b> Second troponin was ordered "
        "but result has not been recorded in chart.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Medications
    story.append(Paragraph("Current Medications", styles['SectionHeader']))
    med_data = [
        ['Medication', 'Dose', 'Route', 'Frequency'],
        ['Aspirin', '300mg', 'Oral', 'STAT (given at 07:00)'],
        ['GTN', '0.4mg', 'Sublingual', 'PRN for chest pain'],
        ['Metoprolol', '25mg', 'Oral', 'BD (twice daily)'],
        ['Enoxaparin', '60mg', 'Subcutaneous', 'BD'],
    ]
    story.append(make_vitals_table(med_data, col_widths=[120, 80, 80, 140]))
    story.append(Spacer(1, 8))

    # Pain Assessment
    story.append(Paragraph("Pain Assessment", styles['SectionHeader']))
    story.append(Paragraph(
        "Chest pain score: <b>6/10 at 08:00</b>, reduced to <b>3/10 at 10:00</b> "
        "after GTN administration. Reported as <b>2/10 at 14:00</b>.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Clinical notes
    story.append(Paragraph("Clinical Notes", styles['SectionHeader']))
    story.append(Paragraph(
        "Patient resting comfortably. Chest pain reduced post-GTN. However, "
        "BP trend is concerning and should be closely monitored. IV access patent "
        "in right antecubital fossa. Cardiac monitor in situ — occasional PVCs noted. "
        "Family (son) at bedside, informed of admission. Consultant review requested "
        "for 16:00.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Report generated: 2024-11-14 at 19:00 | Shift: Day (07:00-19:00) | "
        "Nurse: RN Aisha Patel",
        styles['ClinicalNote']
    ))

    doc.build(story)
    print(f"  [OK] Generated: {output_path}")


def generate_patient_c(output_path):
    """
    Patient C: Ravi Kumar — Routes directly to Synthesis Agent
    Stable UTI patient, all fields complete, discharge candidate.
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           topMargin=30*mm, bottomMargin=20*mm,
                           leftMargin=20*mm, rightMargin=20*mm)
    styles = get_styles()
    story = []

    # Header
    story.append(Paragraph("PATIENT CLINICAL REPORT", styles['ClinicalTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2f855a')))
    story.append(Spacer(1, 12))

    # Demographics
    story.append(Paragraph("Patient Demographics", styles['SectionHeader']))
    info_data = [
        ['Patient ID:', 'PAT-C-2024-1203'],
        ['Full Name:', 'Ravi Kumar'],
        ['Age:', '45 years'],
        ['Gender:', 'Male'],
        ['Ward:', 'General Medicine - Bed 22B'],
        ['Admission Date:', '2024-11-12'],
        ['Admitting Doctor:', 'Dr. Neha Sharma'],
    ]
    story.append(make_info_table(info_data))
    story.append(Spacer(1, 10))

    # Admission reason
    story.append(Paragraph("Admission Reason", styles['SectionHeader']))
    story.append(Paragraph(
        "Admitted with <b>uncomplicated urinary tract infection (UTI)</b>. "
        "Presented with dysuria, increased frequency, and low-grade fever. "
        "Urine culture positive for E. coli, sensitive to trimethoprim. "
        "Commenced on oral antibiotics.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Vitals — all stable
    story.append(Paragraph("Vital Signs", styles['SectionHeader']))
    vitals_data = [
        ['Time', 'Blood Pressure', 'Heart Rate', 'Temp (°C)', 'SpO2 (%)'],
        ['08:00', '128/80', '72', '36.9', '99'],
        ['12:00', '126/78', '70', '36.8', '99'],
        ['16:00', '130/82', '74', '36.9', '99'],
    ]
    story.append(make_vitals_table(vitals_data))
    story.append(Paragraph(
        "All vital signs within normal range. Temperature normalised since Day 1 "
        "of antibiotic therapy.",
        styles['ClinicalNote']
    ))
    story.append(Spacer(1, 8))

    # Pain Assessment
    story.append(Paragraph("Pain Assessment", styles['SectionHeader']))
    story.append(Paragraph(
        "Pain score: <b>2/10</b> (mild suprapubic discomfort, improving). "
        "No analgesic required.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Medications
    story.append(Paragraph("Current Medications", styles['SectionHeader']))
    med_data = [
        ['Medication', 'Dose', 'Route', 'Frequency'],
        ['Trimethoprim', '200mg', 'Oral', 'BD (Day 2 of 5)'],
    ]
    story.append(make_vitals_table(med_data, col_widths=[120, 80, 80, 140]))
    story.append(Spacer(1, 8))

    # Investigations
    story.append(Paragraph("Investigations", styles['SectionHeader']))
    story.append(Paragraph(
        "Urine culture (2024-11-12): E. coli >10⁵ CFU/mL. Sensitive to "
        "trimethoprim, nitrofurantoin, ciprofloxacin. Resistant to amoxicillin.",
        styles['ClinicalBody']
    ))
    story.append(Paragraph(
        "Blood tests (2024-11-13): WCC 9.2 (normalising), CRP 18 (down from 45 "
        "on admission). Renal function normal.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 8))

    # Clinical notes
    story.append(Paragraph("Clinical Notes", styles['SectionHeader']))
    story.append(Paragraph(
        "Patient responding well to antibiotic therapy. Afebrile for 24 hours. "
        "Oral intake good, mobilising independently. No urinary catheter in situ. "
        "Plan: continue trimethoprim for remaining 3 days as outpatient. "
        "<b>Due for discharge tomorrow (2024-11-15)</b> pending consultant review. "
        "Discharge summary and medication reconciliation completed.",
        styles['ClinicalBody']
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Report generated: 2024-11-14 at 19:00 | Shift: Day (07:00-19:00) | "
        "Nurse: RN Vijay Nair",
        styles['ClinicalNote']
    ))

    doc.build(story)
    print(f"  [OK] Generated: {output_path}")


if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)

    print("Generating demo patient PDFs...")
    generate_patient_a(os.path.join(output_dir, "patient_A.pdf"))
    generate_patient_b(os.path.join(output_dir, "patient_B.pdf"))
    generate_patient_c(os.path.join(output_dir, "patient_C.pdf"))
    print("\nAll demo PDFs generated successfully!")
