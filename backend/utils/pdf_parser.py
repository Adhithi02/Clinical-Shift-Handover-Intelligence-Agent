"""
PDF parser using pdfplumber to extract structured patient data from clinical reports.
Handles tables (vitals), demographics, medications, and clinical notes.
"""
import re
import logging
import pdfplumber

logger = logging.getLogger(__name__)


def extract_patient_data(file_path: str) -> dict:
    """
    Extract structured patient data from a clinical report PDF.
    
    Args:
        file_path: Path to the PDF file
    
    Returns:
        Structured dict with patient demographics, vitals, medications, etc.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            tables = []
            
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"
                
                # Extract tables from each page
                page_tables = page.extract_tables() or []
                tables.extend(page_tables)
        
        # Parse structured data from the extracted text
        patient = {
            "file_path": file_path,
            "raw_text": full_text,
            "patient_id": _extract_field(full_text, r'Patient ID[:\s]+([A-Z0-9\-]+)'),
            "name": _extract_field(full_text, r'Full Name[:\s]+([A-Za-z\s]+?)(?:\n|$)'),
            "age": _extract_field(full_text, r'Age[:\s]+(\d+)'),
            "gender": _extract_field(full_text, r'Gender[:\s]+(Male|Female|Other)'),
            "ward": _extract_field(full_text, r'Ward[:\s]+(.+?)(?:\n|$)'),
            "admission_date": _extract_field(full_text, r'Admission Date[:\s]+([\d\-]+)'),
            "admitting_doctor": _extract_field(full_text, r'Admitting Doctor[:\s]+(.+?)(?:\n|$)'),
            "admission_reason": _extract_admission_reason(full_text),
            "vitals": _extract_vitals(full_text, tables),
            "medications": _extract_medications(full_text, tables),
            "pain_score": _extract_pain_score(full_text),
            "procedures": _extract_procedures(full_text),
            "investigations": _extract_investigations(full_text),
            "clinical_notes": _extract_clinical_notes(full_text),
            "missing_flags": _detect_missing_flags(full_text),
        }
        
        # Clean up None values
        for key in patient:
            if patient[key] is None and key not in ['raw_text', 'vitals', 'medications', 'missing_flags']:
                patient[key] = ""
        
        logger.info(f"Extracted data for patient: {patient.get('name', 'Unknown')} ({patient.get('patient_id', 'N/A')})")
        return patient
        
    except Exception as e:
        logger.error(f"Error parsing PDF {file_path}: {e}")
        return {
            "file_path": file_path,
            "error": str(e),
            "raw_text": "",
            "patient_id": "",
            "name": "Parse Error",
            "vitals": [],
            "medications": [],
            "missing_flags": ["PDF parsing failed"]
        }


def _extract_field(text: str, pattern: str) -> str:
    """Extract a single field using regex."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_admission_reason(text: str) -> str:
    """Extract the admission reason section."""
    # Look for text between "Admission Reason" header and next section
    match = re.search(
        r'Admission Reason\s*\n(.+?)(?=\n(?:Vital|Pain|Current Med|Investigation|Clinical Note|Patient Dem))',
        text, re.DOTALL | re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return ""


def _extract_vitals(text: str, tables: list) -> list:
    """
    Extract vital signs from tables and text.
    Returns list of dicts with time, bp, hr, temp, spo2.
    """
    vitals = []
    
    # Try to extract from tables first
    for table in tables:
        if not table or len(table) < 2:
            continue
        
        header = [str(cell).lower() if cell else "" for cell in table[0]]
        
        # Check if this is a vitals table
        is_vitals = any(keyword in " ".join(header) for keyword in 
                       ['blood pressure', 'heart rate', 'temp', 'spo2', 'time'])
        
        if is_vitals:
            for row in table[1:]:
                if not row or not any(row):
                    continue
                cells = [str(cell).strip() if cell else "" for cell in row]
                vital = _parse_vital_row(cells, header)
                if vital:
                    vitals.append(vital)
    
    # Fallback: extract from text if no tables found
    if not vitals:
        vitals = _extract_vitals_from_text(text)
    
    return vitals


def _parse_vital_row(cells: list, header: list) -> dict:
    """Parse a single row of vitals data."""
    vital = {}
    
    for i, h in enumerate(header):
        if i >= len(cells):
            break
        value = cells[i]
        
        if 'time' in h:
            vital['time'] = value
        elif 'blood' in h or 'bp' in h or 'pressure' in h:
            vital['bp'] = value
        elif 'heart' in h or 'hr' in h or 'rate' in h:
            vital['hr'] = value
        elif 'temp' in h:
            vital['temp'] = value
        elif 'spo2' in h or 'o2' in h:
            vital['spo2'] = value
    
    return vital if vital.get('time') else None


def _extract_vitals_from_text(text: str) -> list:
    """Fallback: extract vitals from plain text using regex."""
    vitals = []
    
    # Pattern: time followed by BP reading
    pattern = r'(\d{2}:\d{2})\s+(?:BP\s+)?(\d{2,3}/\d{2,3})'
    matches = re.finditer(pattern, text)
    
    for match in matches:
        time_val = match.group(1)
        bp_val = match.group(2)
        
        # Try to find HR, temp, SpO2 near this time
        line_pattern = rf'{re.escape(time_val)}.*?(?:\n|$)'
        line_match = re.search(line_pattern, text)
        line_text = line_match.group(0) if line_match else ""
        
        hr_match = re.search(r'(?:HR\s+)?(\d{2,3})(?:\s|,)', line_text)
        temp_match = re.search(r'(\d{2}\.\d)', line_text)
        spo2_match = re.search(r'(\d{2,3})%', line_text)
        
        vitals.append({
            'time': time_val,
            'bp': bp_val,
            'hr': hr_match.group(1) if hr_match else '',
            'temp': temp_match.group(1) if temp_match else '',
            'spo2': spo2_match.group(1) if spo2_match else ''
        })
    
    return vitals


def _extract_medications(text: str, tables: list) -> list:
    """Extract medications from tables or text."""
    medications = []
    
    # Try tables first
    for table in tables:
        if not table or len(table) < 2:
            continue
        
        header = [str(cell).lower() if cell else "" for cell in table[0]]
        
        is_med = any(keyword in " ".join(header) for keyword in 
                    ['medication', 'drug', 'dose', 'route', 'frequency'])
        
        if is_med:
            for row in table[1:]:
                if not row or not any(row):
                    continue
                cells = [str(cell).strip() if cell else "" for cell in row]
                med = {}
                for i, h in enumerate(header):
                    if i >= len(cells):
                        break
                    if 'med' in h or 'drug' in h:
                        med['name'] = cells[i]
                    elif 'dose' in h:
                        med['dose'] = cells[i]
                    elif 'route' in h:
                        med['route'] = cells[i]
                    elif 'freq' in h:
                        med['frequency'] = cells[i]
                if med.get('name'):
                    medications.append(med)
    
    # Fallback: extract from text
    if not medications:
        med_section = re.search(
            r'(?:Current )?Medications?\s*\n(.+?)(?=\n(?:Clinical|Investigation|Pain|Vital)|\Z)',
            text, re.DOTALL | re.IGNORECASE
        )
        if med_section:
            for line in med_section.group(1).strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Medication') and len(line) > 3:
                    medications.append({'name': line, 'dose': '', 'route': '', 'frequency': ''})
    
    return medications


def _extract_pain_score(text: str) -> dict:
    """Extract pain score information."""
    pain_info = {
        "scores": [],
        "last_recorded": "",
        "missing_post_op": False
    }
    
    # Find all pain scores
    score_pattern = r'(\d+)/10\s*(?:at\s+(\d{2}:\d{2}))?'
    matches = re.finditer(score_pattern, text)
    
    for match in matches:
        score = int(match.group(1))
        time_val = match.group(2) if match.group(2) else ""
        pain_info["scores"].append({"score": score, "time": time_val})
    
    if pain_info["scores"]:
        pain_info["last_recorded"] = pain_info["scores"][-1].get("time", "")
    
    # Check for missing post-op pain assessment
    if re.search(r'(?:post[- ]?op(?:erative)?.*(?:missing|not\s+(?:been\s+)?documented))|(?:missing.*pain)', 
                 text, re.IGNORECASE):
        pain_info["missing_post_op"] = True
    
    return pain_info


def _extract_procedures(text: str) -> list:
    """Extract procedure history."""
    procedures = []
    
    procedure_patterns = [
        r'((?:right|left)\s+(?:total\s+)?knee\s+replacement)',
        r'((?:surgery|procedure)\s+(?:performed|completed)\s+(?:on\s+)?[\d\-]+\s+at\s+[\d:]+)',
        r'((?:right|left)\s+(?:total\s+)?(?:hip|knee|shoulder)\s+(?:replacement|arthroplasty))',
    ]
    
    for pattern in procedure_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            procedures.append(match.group(1).strip())
    
    return procedures


def _extract_investigations(text: str) -> list:
    """Extract investigation results."""
    investigations = []
    
    inv_section = re.search(
        r'Investigations?\s*\n(.+?)(?=\n(?:Clinical|Pain|Current Med|Patient Dem)|\Z)',
        text, re.DOTALL | re.IGNORECASE
    )
    
    if inv_section:
        for line in inv_section.group(1).strip().split('\n'):
            line = line.strip()
            if line and len(line) > 5:
                investigations.append(line)
    
    return investigations


def _extract_clinical_notes(text: str) -> str:
    """Extract clinical notes section."""
    match = re.search(
        r'Clinical Notes?\s*\n(.+?)(?=\nReport generated|\Z)',
        text, re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else ""


def _detect_missing_flags(text: str) -> list:
    """Detect explicitly flagged missing information in the report."""
    flags = []
    
    missing_patterns = [
        (r'(?:MISSING|NOT DOCUMENTED|not been documented|not recorded)', "Documentation gap detected"),
        (r'no\s+post[- ]?op(?:erative)?\s+pain', "Missing post-operative pain assessment"),
        (r'troponin.*not\s+documented', "Missing troponin result"),
        (r'no\s+medication\s+reconciliation', "Missing medication reconciliation"),
    ]
    
    for pattern, description in missing_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append(description)
    
    return flags
