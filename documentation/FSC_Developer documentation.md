# FSC Developer Plugin
**ISO 26262-3:2018, Clause 7 - Functional Safety Concept**

**Version:** 0.0.1  
**Author:** Tonino De Nigris  
**Repository:** https://github.com/tondeni/AI_Agent-FSC_Developer

---

## OVERVIEW

The FSC Developer plugin enables AI agents to develop Functional Safety Concept (FSC) work products by transforming HARA safety goals into Functional Safety Requirements (FSRs) and allocating them to system architectural elements. The FSC is a critical work product that bridges concept-phase safety goals with technical implementation requirements.

**Key Capabilities:**
- Load and integrate HARA outputs (safety goals with ASIL ratings)
- Develop 9 comprehensive safety strategies per ISO 26262-3:2018
- Derive Functional Safety Requirements (FSRs) in 8 categories
- Allocate FSRs to system architectural elements
- Specify safety validation criteria for each FSR
- Verify FSC completeness and ISO 26262 compliance
- Generate professional FSC documentation (Word + Excel)

**Purpose:**
The Functional Safety Concept specifies what safety measures are needed to achieve each safety goal, without defining how they will be technically implemented. It creates the foundation for Technical Safety Concept development and ensures complete traceability from hazards to safety requirements. This plugin automates FSC development while ensuring full compliance with ISO 26262-3:2018 Clause 7 requirements.

---

## WORKFLOW

### Internal Workflow

The FSC Developer follows a 7-step structured process:

```
1. Load HARA (Safety Goals + ASIL)
    ↓
2. Develop Safety Strategies (9 types per goal)
    ↓
3. Derive Functional Safety Requirements (FSRs)
    ↓
4. Allocate FSRs to Architecture
    ↓
5. Specify Validation Criteria
    ↓
6. Verify FSC Completeness & Compliance
    ↓
7. Generate FSC Documentation (Word + Excel)
```

**Step Details:**

**Step 1: Load HARA**
- Reads safety goals from working memory or Excel/CSV files
- Extracts: Safety Goal, ASIL, Safe State, FTTI
- Validates ASIL ratings (A, B, C, D)
- Stores in working memory for FSC development

**Step 2: Develop Safety Strategies**
- Creates 9 safety strategies per ISO 26262-3:2018, Clause 7.4.2.3:
  - Fault Avoidance, Detection, Control
  - Safe State Transition, Fault Tolerance
  - Degradation, Driver Warnings (×2)
  - Timing (FTTI), Arbitration
- Each strategy specifies approach to achieve safety goal

**Step 3: Derive FSRs**
- Translates strategies into testable requirements
- 8 FSR categories with unique IDs (FSR-XXX-TYPE-n)
- Each FSR includes: requirement text, ASIL, verification method, safe state, FTTI
- Inherits ASIL from parent safety goal

**Step 4: Allocate FSRs**
- Assigns FSRs to system architectural elements
- Element types: E/E Hardware, E/E Software, Mechanical, Other, External
- Ensures freedom from interference
- Maintains ASIL integrity

**Step 5: Specify Validation Criteria**
- Defines acceptance criteria for each FSR
- Links criteria to validation methods per ISO 26262-4
- Specifies test conditions and pass criteria

**Step 6: Verify FSC**
- Checks completeness (all goals have FSRs, all FSRs allocated)
- Validates consistency (ASIL inheritance, safe states)
- Confirms correctness (technical feasibility)
- Verifies traceability (Safety Goals ↔ FSRs ↔ Architecture)
- Assesses ISO 26262-3 compliance

**Step 7: Generate Documentation**
- Creates Word document with all FSC sections
- Generates Excel traceability matrix
- Includes verification report
- Professional formatting with ISO clause references

### Integration with Other Plugins

**Upstream Integration:**

1. **HARA Assistant Plugin**
   - **Data Flow:** Safety Goals → FSC Development
   - **Method:** Working memory, Excel file, or CSV
   - **Use Case:** FSC reads HARA safety goals to derive FSRs
   - **Workflow:**
     ```
     HARA Assistant (generate HARA)
         ↓
     [Working Memory: hara_safety_goals]
     OR
     [File: System_HARA.xlsx]
         ↓
     FSC Developer (load HARA)
         ↓
     Continue FSC workflow
     ```

**Downstream Integration:**

2. **Technical Safety Concept (TSC) Developer** *(Future)*
   - **Data Flow:** FSRs → Technical Requirements
   - **Method:** Working memory or FSC document export
   - **Use Case:** TSC reads FSRs to derive Technical Safety Requirements
   - **Workflow:**
     ```
     FSC Developer (generate FSC)
         ↓
     [Working Memory: functional_safety_requirements]
         ↓
     TSC Developer (load FSC)
     ```

**Complete Safety Lifecycle Chain:**
```
Item Definition Developer
    ↓
HARA Assistant
    ↓
FSC Developer ← You are here
    ↓
TSC Developer (Technical Safety Concept)
    ↓
Software/Hardware Safety Requirements
    ↓
...
```

### Typical Usage Scenarios

**Scenario 1: Full FSC Development**
```
1. "load HARA for Battery Management System"
2. "develop safety strategy for all goals"
3. "derive FSRs for all goals"
4. "allocate all FSRs"
5. "specify validation criteria"
6. "verify FSC"
7. "generate FSC document"
```

**Scenario 2: Chained from HARA Assistant**
```
1. Complete HARA (HARA Assistant plugin)
2. "load HARA for [System]" (reads from working memory)
3. Continue FSC workflow steps 2-7
```

**Scenario 3: File-Based Integration**
```
1. Place HARA Excel file in hara_inputs/ folder
2. "load HARA for [System]"
3. Continue FSC workflow steps 2-7
```

**Scenario 4: Iterative Development**
```
1. Load HARA
2. Develop strategies for ASIL D goals only
3. Review and refine
4. Develop strategies for remaining goals
5. Derive all FSRs
6. Complete workflow
```

---

## FUNCTIONALITIES

### 1. Load HARA for FSC
**Description:** Loads HARA outputs (safety goals with ASIL ratings) from working memory, Excel files, or CSV files. Extracts safety goals, ASIL, safe states, and FTTI values. Validates ASIL ratings and prepares data for FSC development.

**Input:**
- `item_name` (string) - Name of the system (e.g., "Battery Management System")
- HARA data sources (priority order):
  1. Working memory from HARA Assistant
  2. Excel/CSV files in `hara_inputs/` folder
  3. Direct user input

**Output:**
- Loaded safety goals with ASIL ratings
- ASIL distribution summary (count by A/B/C/D)
- Stored in working memory under `fsc_safety_goals`
- Ready for strategy development

---

### 2. Develop Safety Strategy
**Description:** Develops comprehensive safety strategies for each safety goal following ISO 26262-3:2018, Clause 7.4.2.3 requirements. Creates 9 strategy types covering fault avoidance, detection, control, safe states, tolerance, degradation, warnings, timing, and arbitration.

**Input:**
- Safety goals from Step 1
- Optional: Specific safety goal to develop (otherwise develops for all)
- System architecture context

**Output:**
- 9 safety strategies per safety goal
- Each strategy includes: approach, methods, mechanisms, and rationale
- Strategies cover all ISO 26262-3 Clause 7.4.2.3 requirements
- Stored in working memory under `safety_strategies`

---

### 3. Derive Functional Safety Requirements (FSRs)
**Description:** Translates safety strategies into testable Functional Safety Requirements per ISO 26262-8:2018, Clause 6. Creates FSRs in 8 categories with unique IDs, inherits ASIL from safety goals, and specifies verification methods, safe states, and FTTI values.

**Input:**
- Safety strategies from Step 2
- Safety goals with ASIL ratings
- Optional: Focus on specific FSR type

**Output:**
- Complete set of FSRs (typically 30-150 depending on system complexity)
- 8 FSR categories: Fault Avoidance, Detection, Control, Safe State Transition, Fault Tolerance, Warning, Timing, Arbitration
- Each FSR includes: ID, requirement text, ASIL, verification method, operating modes, safe state, FTTI, redundancy, emergency operation
- FSR distribution by ASIL and type
- Stored in working memory under `functional_safety_requirements`

---

### 4. Allocate Functional Requirements
**Description:** Allocates FSRs to system architectural elements per ISO 26262-3:2018, Clause 7.4.2.8. Assigns each FSR to appropriate E/E hardware, software, mechanical, or external elements. Ensures ASIL capability and freedom from interference.

**Input:**
- FSRs from Step 3
- System architecture definition
- Optional: Specific architectural element to allocate

**Output:**
- FSR-to-architecture allocation table
- Architectural element types: E/E Hardware, E/E Software, Mechanical, Other Technologies, External Measures
- Each allocation includes: element name, type, ASIL capability, allocated FSRs
- Allocation completeness verification (100% FSRs allocated)
- Freedom from interference documentation
- Stored in working memory under `fsr_allocation`

---

### 5. Specify Safety Validation Criteria
**Description:** Defines acceptance criteria for safety validation per ISO 26262-3:2018, Clause 7.4.3. Creates validation criteria for each safety goal and FSR, specifying test methods, pass criteria, and validation levels (unit, integration, system, vehicle).

**Input:**
- Safety goals from Step 1
- FSRs from Step 3
- Validation methods from ISO 26262-4

**Output:**
- Validation criteria for each safety goal and FSR
- Each criterion includes: ID, validation method, test environment, pass criteria, test cycles
- Validation level distribution (unit/integration/system/vehicle)
- Coverage analysis (100% safety goals, 100% FSRs)
- Stored in working memory under `validation_criteria`

---

### 6. Verify Functional Safety Concept
**Description:** Performs comprehensive FSC verification per ISO 26262-8:2018, Clause 9 and ISO 26262-3:2018, Clause 7.4.4. Checks completeness, consistency, correctness, traceability, and ISO 26262 compliance. Generates detailed verification report.

**Input:**
- All FSC elements from Steps 1-5
- ISO 26262-3 Clause 7 requirements
- Verification checklist

**Output:**
- Comprehensive verification report with Pass/Fail status
- Completeness check (all goals → FSRs, all FSRs allocated, all criteria defined)
- Consistency check (ASIL inheritance, safe states, FTTI)
- Correctness check (technical feasibility, allocation appropriateness)
- Traceability check (Safety Goals ↔ FSRs ↔ Architecture ↔ Validation)
- ISO 26262-3 compliance assessment (all Clause 7 requirements)
- Overall status: Compliant / Non-Compliant with recommendations

---

### 7. Generate FSC Document
**Description:** Creates complete, ISO 26262-3 compliant FSC documentation including Word document with all sections and Excel traceability matrix. Includes executive summary, strategies, FSRs, allocation, validation criteria, verification report, and traceability matrices.

**Input:**
- All FSC content from Steps 1-6 (stored in working memory)
- System name and metadata
- Optional: Template customization

**Output:**
- **Word Document (.docx):**
  - 8 main sections per ISO 26262-3 Clause 7
  - Executive summary with ASIL distribution
  - All 9 safety strategies for each goal
  - Complete FSR catalog with details
  - Architectural allocation tables
  - Validation criteria specifications
  - Verification report
  - Traceability matrices
  - ISO clause references throughout
- **Excel Workbook (.xlsx):**
  - Sheet 1: Safety Goals → FSRs
  - Sheet 2: FSRs → Architecture
  - Sheet 3: FSRs → Validation Criteria
  - Sheet 4: Complete traceability map
  - Coverage statistics
- Files saved in `generated_documents/05_FSC/` with timestamp
- Professional formatting ready for review and approval

---

## FSC DOCUMENT STRUCTURE

Generated FSC documents include:

### 1. Introduction
- Purpose and scope
- Applicable documents
- Definitions and abbreviations

### 2. Safety Goals
- Safety goal overview
- ASIL summary and distribution
- Safety goal details with ASIL

### 3. Safety Strategies (9 types)
- 3.1 Fault Avoidance Strategy
- 3.2 Fault Detection Strategy
- 3.3 Fault Control Strategy
- 3.4 Safe State Transition Strategy
- 3.5 Fault Tolerance Strategy
- 3.6 Degradation Strategy
- 3.7 Driver Warning Strategy (Exposure)
- 3.8 Driver Warning Strategy (Controllability)
- 3.9 Timing Requirements (FTTI)
- 3.10 Arbitration Strategy

### 4. Functional Safety Requirements
- FSR overview by category
- FSR details (ID, text, ASIL, verification)
- FSR ASIL summary

### 5. Architectural Allocation
- System architecture overview
- FSR-to-component allocation
- Freedom from interference

### 6. Safety Validation Criteria
- Validation approach
- Validation criteria details
- Coverage analysis

### 7. Verification Report
- Verification results
- ISO 26262 compliance assessment
- Recommendations

### 8. Traceability
- Traceability matrices
- Coverage analysis

---

## FSR CATEGORIES

The plugin generates FSRs in 8 ISO 26262-3 compliant categories:

| FSR Type | ID Format | ISO Reference | Purpose |
|----------|-----------|---------------|---------|
| **Fault Avoidance** | FSR-XXX-AVD-n | 7.4.2.3.a | Preventing faults through design |
| **Fault Detection** | FSR-XXX-DET-n | 7.4.2.3.b | Detecting malfunctions |
| **Fault Control** | FSR-XXX-CTL-n | 7.4.2.3.b | Controlling fault effects |
| **Safe State Transition** | FSR-XXX-SST-n | 7.4.2.3.c | Achieving safe state |
| **Fault Tolerance** | FSR-XXX-TOL-n | 7.4.2.3.d | Redundancy/tolerance |
| **Warning/Indication** | FSR-XXX-WRN-n | 7.4.2.3.f,g | Driver warnings |
| **Timing** | FSR-XXX-TIM-n | 7.4.2.3.h | FTTI compliance |
| **Arbitration** | FSR-XXX-ARB-n | 7.4.2.3.i | Control arbitration |

---

## USAGE EXAMPLES

### Example 1: Complete FSC Development
```
User: load HARA for Electric Power Steering

Agent: ✅ HARA Loaded Successfully
System: Electric Power Steering
Safety Goals: 15
ASIL Distribution: D(3), C(5), B(4), A(3)

User: develop safety strategy for all goals

Agent: ✅ Safety Strategies Developed
Strategies Created: 135 (15 goals × 9 strategies)
[Detailed strategies output...]

User: derive FSRs for all goals

Agent: ✅ Functional Safety Requirements Derived
Total FSRs: 68
Distribution by Type:
├─ Fault Avoidance: 12 FSRs
├─ Fault Detection: 18 FSRs
├─ Fault Control: 11 FSRs
[...]

User: allocate all FSRs

Agent: ✅ FSRs Allocated to Architecture
Components: 9
├─ EPS ECU Hardware: 22 FSRs
├─ EPS Software: 28 FSRs
[...]

User: specify validation criteria

Agent: ✅ Validation Criteria Specified
Total Criteria: 83
[Distribution by test level...]

User: verify FSC

Agent: ✅ FSC Verification Complete
Status: ✅ COMPLIANT
[Detailed verification results...]

User: generate FSC document

Agent: ✅ FSC Document Generated
Files Created:
📄 Electric_Power_Steering_FSC_20251007.docx (142 pages)
📊 Electric_Power_Steering_FSC_Traceability_20251007.xlsx
```

---

## HARA FILE FORMATS SUPPORTED

The plugin accepts various HARA file formats:

**Required Columns:**
- Safety Goal (or Goal, SafetyGoal, SG)
- ASIL (or ASIL Rating, ASIL Level)

**Optional Columns:**
- Safe State (or SafeState, SS)
- FTTI (or Fault Tolerant Time)
- Severity, Exposure, Controllability (for reference)
- Hazardous Event (for context)
- Hazard ID (for traceability)

**Missing Data Handling:**
- If Safe State missing: Sets to "To be specified per ISO 26262-3:2018, 7.4.2.5"
- If FTTI missing: Sets to "To be determined per ISO 26262-3:2018, 7.4.2.4.b"

---

## FILE STRUCTURE

```
AI_Agent-FSC_Developer/
├── plugin.json
├── README.md
├── fsc_tool_main.py                # Main FSC tools
├── fsc_tool_allocation.py          # Allocation logic
├── fsc_tool_verification.py        # Verification
├── fsc_doc_generator.py            # Document generation
├── utils.py                        # Helper functions
├── templates/
│   ├── fsc_structure.json          # FSC structure
│   └── verification_methods.json   # Verification templates
├── hara_inputs/                    # HARA files
├── generated_documents/
│   └── 05_FSC/                     # FSC outputs
└── assets/
    └── FuSa_AI_Agent_Plugin_logo.png
```

---

## ISO 26262 COMPLIANCE

This plugin implements:

- ✅ **ISO 26262-3:2018, Clause 7.1** - FSC objectives
- ✅ **ISO 26262-3:2018, Clause 7.4.2** - FSR specification
  - ✅ 7.4.2.1 - FSRs per ISO 26262-8
  - ✅ 7.4.2.2 - At least one FSR per safety goal
  - ✅ 7.4.2.3 - All 9 strategy types (a-i)
  - ✅ 7.4.2.4 - All 5 FSR considerations
  - ✅ 7.4.2.5-7 - Safe states, emergency operation, driver actions
  - ✅ 7.4.2.8 - Architectural allocation
- ✅ **ISO 26262-3:2018, Clause 7.4.3** - Validation criteria
- ✅ **ISO 26262-3:2018, Clause 7.4.4** - FSC verification
- ✅ **ISO 26262-3:2018, Clause 7.5** - Work products
- ✅ **ISO 26262-8:2018, Clause 6** - Requirements specification
- ✅ **ISO 26262-8:2018, Clause 9** - Verification methods

---

## BEST PRACTICES

1. **Complete HARA First:** Ensure HARA is reviewed and approved before FSC
2. **Iterative Development:** Start with highest ASIL goals
3. **Validate Strategies:** Review strategies with system architects
4. **Verify ASIL Integrity:** Ensure ASIL maintained through allocation
5. **Define Architecture Early:** Have preliminary architecture before allocation
6. **Document Assumptions:** Record all technical assumptions
7. **100% Traceability:** Ensure complete traceability chains
8. **Review Before Generation:** Run verify_fsc before generating documents

---

## INTEGRATION TIPS

**With HARA Assistant:**
- Complete HARA workflow fully
- Generate HARA document or keep in working memory
- Use exact system name for seamless integration

**Quality Gates:**
- HARA must be ≥90% compliant (HARA Reviewer)
- All ASIL D safety goals must have strategies
- FSC verification must show "Compliant" status
- 100% FSR allocation required

**For Manual Integration:**
- Export HARA to Excel with standard column names
- Place in hara_inputs/ folder
- Proceed with FSC workflow

---

## TROUBLESHOOTING

**Issue:** "No HARA found"
- **Solution:** Check file location in hara_inputs/ folder
- Verify filename contains system name
- Check file format (.xlsx or .csv)

**Issue:** FSRs not inheriting correct ASIL
- **Solution:** Verify ASIL column in HARA contains A/B/C/D
- Check for typos (e.g., "ASIL_D" instead of "D")
- Re-load HARA with correct format

**Issue:** Allocation incomplete
- **Solution:** Define all architectural elements
- Ensure elements have ASIL capability
- Run allocation for all FSRs

**Issue:** Verification fails
- **Solution:** Check completeness (all goals → FSRs)
- Verify all FSRs allocated
- Ensure validation criteria defined

---

## LIMITATIONS

- Generated FSRs should be reviewed by safety engineers
- Architectural allocation requires defined system architecture
- Plugin generates content based on ISO 26262 patterns; technical validation required
- Not a replacement for safety engineering expertise
- Verification checks structure, not technical correctness

---

## FUTURE ENHANCEMENTS

**Planned Features:**
- ASIL decomposition tool (ISO 26262-9)
- Safety mechanism catalog integration
- Technical Safety Concept (TSC) generation
- Hardware safety metrics calculation
- Advanced traceability visualization

---

## SUPPORT

**GitHub:** https://github.com/tondeni/AI_Agent-FSC_Developer  
**Issues:** Report issues via GitHub Issues  
**Author:** Tonino De Nigris

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**ISO 26262 Edition:** 2018 (2nd Edition)