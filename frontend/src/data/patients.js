export const DEMO_PATIENTS = [
  {
    id: "A",
    name: "Arun Mehta",
    age: 58,
    condition: "POST-SURGERY",
    conditionColor: "amber",
    vitals: [
      { label: "BP",   value: "124/82", status: "normal" },
      { label: "HR",   value: "76 bpm", status: "normal" },
      { label: "Temp", value: "37.1°C", status: "normal" },
      { label: "O2",   value: "98%",    status: "normal" }
    ],
    alert: {
      type: "warning",
      text: "Pain score not recorded since pre-op (09:00). Surgery at 14:00."
    },
    raw_text: `Patient: Arun Mehta, 58M. 
    Admitted for right knee replacement surgery performed at 14:00.
    Pre-op vitals: BP 124/82, HR 76, Temp 37.1, O2 98%.
    Medications: Paracetamol 1g QID, Enoxaparin 40mg OD.
    Pain score recorded at 09:00: 4/10.
    No pain score recorded post-surgery.
    Wound site: clean, no signs of infection.`
  },
  {
    id: "B",
    name: "Priya Sharma",
    age: 71,
    condition: "CARDIAC MONITORING",
    conditionColor: "red",
    vitals: [
      { label: "BP 08:00", value: "138/88", status: "normal" },
      { label: "BP 10:00", value: "131/84", status: "normal" },
      { label: "BP 12:00", value: "122/79", status: "warning" },
      { label: "BP 14:00", value: "114/72", status: "danger" }
    ],
    alert: {
      type: "danger",
      text: "Declining BP trend over 6 hours: 138→131→122→114 mmHg"
    },
    raw_text: `Patient: Priya Sharma, 71F.
    Admitted with chest pain, query ACS.
    BP readings: 08:00=138/88, 10:00=131/84, 12:00=122/79, 14:00=114/72
    HR 88, O2 96%, Temp 37.0.
    Medications: Aspirin 300mg, GTN PRN, Metoprolol 25mg BD.
    Troponin result pending — no result documented after 12:00.
    ECG: sinus rhythm, no ST changes noted at admission.`
  },
  {
    id: "C",
    name: "Ravi Kumar",
    age: 45,
    condition: "UTI — STABLE",
    conditionColor: "green",
    vitals: [
      { label: "BP",   value: "128/80", status: "normal" },
      { label: "HR",   value: "72 bpm", status: "normal" },
      { label: "Temp", value: "36.9°C", status: "normal" },
      { label: "O2",   value: "99%",    status: "normal" }
    ],
    alert: {
      type: "success",
      text: "All fields complete. Responding well. Due for discharge tomorrow."
    },
    raw_text: `Patient: Ravi Kumar, 45M.
    Admitted with urinary tract infection.
    Vitals stable: BP 128/80, HR 72, Temp 36.9, O2 99%.
    Pain score: 2/10.
    Medications: Trimethoprim 200mg BD (day 2 of 5).
    Urine culture pending. Patient tolerating oral medications.
    All documentation complete. Planned discharge tomorrow morning.`
  }
]
