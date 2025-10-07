# FSC Developer Plugin - Complete Usage Guide

## Quick Start with Your HARA File

### Step 1: Place Your HARA File

You have a HARA file named `Wiper_HARA.xlsx`. Place it in the plugin folder:

```
plugins/AI_Agent-FSC_Developer/hara_inputs/Wiper_HARA.xlsx
```

**The plugin will automatically:**
- Detect the file
- Find the correct worksheet (looks for sheets with "HARA", "Hazard", "Risk" in the name)
- Parse columns flexibly (handles various naming conventions)
- Extract safety goals with ASIL ratings

### Step 2: Start FSC Development

Simply tell the agent:

```
load HARA for Wiper System
```

or if your file is already in place:

```
load HARA for Wiper
```

**What happens:**
- Plugin searches for files containing "wiper" in `hara_inputs/` folder
- Reads `Wiper_HARA.xlsx`
- Extracts all safety goals with ASIL A/B/C/D
- Skips QM (Quality Management) rows
- Validates data per ISO 26262-3:2018

### Step 3: Follow the Complete Workflow

After loading HARA, execute the remaining steps:

```
1. develop safety strategy for all goals
2. derive FSRs for all goals
3. allocate all FSRs
4. specify validation criteria
5. verify FSC
6. generate FSC document
```

---

## Supported HARA File Formats

### Column Names (Flexible Recognition)

The plugin recognizes multiple naming conventions:

| Data | Recognized Column Names |
|------|------------------------|
| **Hazard ID** | "Hazard ID", "Hazard_ID", "HazardID", "Haz ID", "ID" |
| **Function/Item** | "Function", "Item", "System", "Component" |
| **Hazardous Event** | "Hazardous Event", "Hazard Event", "Event", "Hazard" |
| **Operational Situation** | "Operational Situation", "Operation", "Situation", "Scenario" |
| **Severity** | "S", "Severity", "Sev" |
| **Exposure** | "E", "Exposure", "Exp" |
| **Controllability** | "C", "Controllability", "Control", "Ctrl" |
| **ASIL** | "ASIL", "ASIL Rating", "ASIL Level" |
| **Safety Goal** | "Safety Goal", "SafetyGoal", "Safety Goals", "Goal", "SG" |
| **Safe State** | "Safe State", "SafeState", "SS" |
| **FTTI** | "FTTI", "Fault Tolerant Time", "Time Interval" |

### Example HARA Formats Supported

**Format 1: Standard ISO 26262 Format**
```
| Hazard ID | Function | Hazardous Event | S | E | C | ASIL | Safety Goal | Safe State | FTTI |
```

**Format 2: Condensed Format**
```
| ID | Item | Event | Severity | Exposure | Control | ASIL | Goal |
```

**Format 3: Your Wiper Format**
The plugin will automatically detect and parse your specific format!

---

## What the Plugin Extracts

From your HARA file, the plugin extracts:

### Required Fields (Must Have)
- ✅ **Safety Goal** - The safety objective
- ✅ **ASIL** - Risk classification (A, B, C, or D)

### Optional Fields (Nice to Have)
- **Safe State** - If not provided, will be specified during FSC development
- **FTTI** - If not provided, will be determined during FSC development
- **Severity, Exposure, Controllability** - For reference
- **Hazardous Event** - For context
- **Operational Situation** - For context

### What Happens with Missing Data

| Missing Field | Plugin Behavior |
|--------------|-----------------|
| Safe State | Sets to: "To be specified per ISO 26262-3:2018, 7.4.2.5" |
| FTTI | Sets to: "To be determined per ISO 26262-3:2018, 7.4.2.4.b" |
| S, E, C | Stores as empty, still processes safety goal |
| Hazard ID | Auto-generates: "H-001", "H-002", etc. |

---

## Complete Workflow Example

### For Wiper System

```
User: load HARA for Wiper System

Agent: ✅ HARA Loaded Successfully
       System: Wiper System
       Safety Goals Extracted: 8
       
       ASIL Distribution:
       - ASIL D: 2 goals
       - ASIL C: 3 goals
       - ASIL B: 3 goals

User: develop safety strategy for all goals

Agent: ✅ Functional Safety Strategies Developed
       [Detailed strategies for fault avoidance, detection, control, 
        safe state transitions, fault tolerance, degradation, 
        driver warnings, timing, and arbitration]

User: derive FSRs for all goals

Agent: ✅ Functional Safety Requirements Derived
       Total FSRs: 35
       - Fault Avoidance: 8 FSRs
       - Fault Detection: 8 FSRs
       - Fault Control: 5 FSRs
       - Safe State Transition: 8 FSRs
       - Fault Tolerance: 3 FSRs
       - Warning/Indication: 2 FSRs
       - Timing: 1 FSR

User: allocate all FSRs

Agent: ✅ FSRs Allocated to System Components
       - Wiper Motor Controller: 12 FSRs
       - Position Sensor: 6 FSRs
       - Wiper ECU Software: 8 FSRs
       - HMI: 2 FSRs
       - Vehicle CAN Gateway: 7 FSRs

User: specify validation criteria

Agent: ✅ Safety Validation Criteria Specified
       Validation Criteria Defined: 43
       [Criteria for each safety goal and FSR]

User: verify FSC

Agent: ✅ FSC Verification Complete
       Verification Status: ✅ COMPLIANT
       [Detailed verification report]

User: generate FSC document

Agent: ✅ Functional Safety Concept Generated
       Files Created:
       - Wiper_System_FSC_20251007_143022.docx
       - Wiper_System_FSC_Traceability_20251007_143022.xlsx
```

---

## Troubleshooting

### Issue 1: "No HARA found"

**Problem:** Plugin can't find your HARA file

**Solutions:**
1. Check file location: `plugins/AI_Agent-FSC_Developer/hara_inputs/`
2. Ensure file format: `.xlsx` or `.xls`
3. Try exact item name: "Wiper" if file is "Wiper_HARA.xlsx"
4. Check if file has "HARA" or "Wiper" in the name

### Issue 2: "No valid safety goals found"

**Problem:** HARA file loaded but no safety goals extracted

**Possible Causes:**
- All rows have ASIL = QM (no A/B/C/D)
- Safety Goal column is empty
- Wrong worksheet selected

**Solutions:**
1. Ensure at least one row has ASIL A, B, C, or D
2. Check Safety Goal column has text
3. Rename sheet to include "HARA" or "Safety" in the name

### Issue 3: Column names not recognized

**Problem:** Plugin can't find columns

**Solution:**
The plugin is very flexible! But if issues persist:
- Use standard column names: "ASIL", "Safety Goal"
- Or rename columns to include keywords like "Goal", "ASIL", "Hazard"
- Minimum required: columns with "ASIL" and "Safety Goal" or "Goal"

---

## Advanced Features

### 1. Multiple HARA Files

Place multiple HARA files in `hara_inputs/`:
- `Wiper_HARA.xlsx`
- `Brake_HARA.xlsx`
- `Steering_HARA.xlsx`

Load specific one:
```
load HARA for Wiper System    # Loads Wiper_HARA.xlsx
load HARA for Brake System    # Loads Brake_HARA.xlsx
```

### 2. Working with Incomplete HARAs

If your HARA is missing Safe States or FTTI:
- ✅ Plugin will still load it
- ✅ Sets placeholder values per ISO 26262-3
- ✅ You can specify them during strategy development
- ✅ FSC development continues normally

### 3. Review Specific Items

After loading:
```
show safety goal SG-001        # View specific goal
show strategy for SG-003       # View specific strategy
show FSR FSR-001-DET-1        # View specific FSR
show allocation summary        # View all allocations
```

### 4. Partial Workflow

You can do partial workflows:
```
# Just develop strategies
load HARA for Wiper
develop safety strategy for SG-002

# Just derive FSRs for one goal
derive FSRs for SG-003

# Allocate specific FSR
allocate FSR-001-DET-1 to Wiper Motor Controller
```

---

## Generated Documents

### 1. FSC Document (.docx)

**Sections:**
1. Introduction and Scope
2. Referenced Documents (HARA, Item Definition, ISO 26262)
3. Safety Goals Overview (table)
4. Functional Safety Strategies (detailed for each goal)
5. Functional Safety Requirements (FSRs by category)
6. FSR Allocation Matrix (by component)
7. Traceability Matrix (SG → FSR)
8. Validation Criteria
9. Verification Report
10. Approvals Section

**Format:** Professional Word document, ISO 26262-3:2018 compliant

### 2. FSR Traceability Matrix (.xlsx)

**Sheets:**
- **FSR Matrix:** All FSRs with full details
  - Columns: FSR-ID, Description, Type, ASIL, Safety Goal, Allocated To, FTTI, Verification
  
- **Safety Goals:** Summary of all goals
  - Columns: SG-ID, Safety Goal, ASIL, Safe State, FTTI, FSR Count
  
- **Allocation Matrix:** Components and their FSRs
  - Columns: Component, Type, FSR Count, ASIL Levels, FSR IDs

**Format:** Excel workbook with headers, ready for filtering/sorting

---

## ISO 26262-3:2018 Compliance

### What the Plugin Ensures

✅ **7.3.1 Prerequisites**
- HARA report loaded and validated

✅ **7.4.2 FSR Derivation**
- All 9 strategies specified (7.4.2.3 a-i)
- All 5 FSR criteria considered (7.4.2.4 a-e)
- At least one FSR per safety goal (7.4.2.2)

✅ **7.4.2.8 FSR Allocation**
- FSRs allocated to architectural elements
- ASIL inheritance from safety goals
- Freedom from interference considered

✅ **7.4.3 Safety Validation Criteria**
- Acceptance criteria specified
- Based on FSRs and safety goals

✅ **7.4.4 FSC Verification**
- Consistency checked
- Compliance verified
- Hazard mitigation assessed

✅ **7.5 Work Products**
- Functional Safety Concept document
- Verification report
- Traceability matrix

---

## Tips for Best Results

### 1. HARA Quality
- Ensure clear, specific safety goals
- Include ASIL ratings (A/B/C/D)
- Add safe states if known
- Specify FTTI if available

### 2. Strategy Development
- Let the AI generate comprehensive strategies
- Review and refine if needed
- Ensure all 9 strategy types are covered

### 3. FSR Derivation
- Aim for 5-10 FSRs per safety goal
- Make FSRs measurable and testable
- Include all required considerations

### 4. Allocation
- Think about actual system architecture
- Group related FSRs to same component
- Consider HW vs SW implementation

### 5. Documentation
- Generate document after completing all steps
- Review for completeness
- Obtain necessary approvals

---

## Support and References

### Plugin Documentation
- README.md - Overview and quick start
- ISO_26262_Compliance_Summary.md - Full compliance details

### ISO 26262 References
- ISO 26262-3:2018, Clause 7 - Functional Safety Concept
- ISO 26262-4:2018, Clause 8 - Safety Validation
- ISO 26262-8:2018, Clause 6 - Requirements Specification
- ISO 26262-8:2018, Clause 9 - Verification

### Key Terms
- **FSC:** Functional Safety Concept
- **FSR:** Functional Safety Requirement
- **ASIL:** Automotive Safety Integrity Level
- **FTTI:** Fault Tolerant Time Interval
- **SG:** Safety Goal

---

## Example Commands Reference

```bash
# Load HARA
load HARA for Wiper System
load HARA for [Your System Name]

# Show workflow
show FSC workflow
help with FSC

# Develop strategies
develop safety strategy for all goals
develop safety strategy for SG-001

# Derive FSRs
derive FSRs for all goals
derive FSRs for SG-002

# Allocate FSRs
allocate all FSRs
allocate FSR-001-DET-1 to Wiper Motor Controller

# Validation & Verification
specify validation criteria
verify FSC

# Generate documents
generate FSC document

# View items
show safety goal SG-001
show FSR FSR-001-DET-1
show allocation summary
```

---

**Version:** 1.0  
**Last Updated:** October 2025  
**Plugin:** AI_Agent-FSC_Developer  
**ISO Standard:** ISO 26262-3:2018