# Functional Safety Concept Assistant Plugin - Design Specification

## Overview
This plugin guides users through the creation of a complete, ISO 26262-4:2018 compliant Functional Safety Concept by transforming HARA safety goals into technical requirements and allocating them to architectural elements.

---

## Plugin Metadata

```json
{
  "name": "[Kineton] ISO 26262 FSC Developer",
  "version": "0.0.1",
  "description": "A plugin that enables AI agents to develop a Functional Safety Concept work product from HARA outputs, compliant with ISO 26262-4:2018",
  "author_name": "Tonino De Nigris",
  "author_url": "https://github.com/tondeni",
  "plugin_url": "https://github.com/tondeni/AI_Agent-FSC_Developer",
  "tags": "ISO26262, FuSa, Functional Safety, FSC",
  "thumb": "https://github.com/tondeni/AI_Agent-FSC_Developer/blob/master/assets/FuSa_AI_Agent_Plugin_logo.png?raw=true"
}
```

---

## Plugin Structure

```
AI_Agent-FSC_Developer/
├── plugin.json
├── README.md
├── requirements.txt
├── assets/
│   └── FuSa_AI_Agent_Plugin_logo.png
├── templates/
│   ├── fsc_structure.json                    # FSC document structure
│   ├── safety_mechanisms_catalog.json        # Pre-defined safety mechanisms
│   ├── asil_decomposition_rules.json         # ASIL decomposition guidance
│   ├── verification_methods.json             # Verification strategy templates
│   └── architectural_patterns.json           # Common safety architectures
├── checklists/
│   └── fsc_completeness_checklist.json       # ISO 26262-4 compliance
├── generated_documents/
│   ├── 05_FSC/                               # Generated FSC documents
│   └── 00_Templates/                         # Template outputs
├── hara_inputs/                              # HARA files to process
├── fsc_tool_main.py                          # Main FSC development tool
├── fsc_tool_allocation.py                    # FSR allocation logic
├── fsc_tool_mechanisms.py                    # Safety mechanism identification
├── fsc_tool_decomposition.py                 # ASIL decomposition tool
├── fsc_tool_verification.py                  # Verification strategy tool
├── fsc_doc_generator.py                      # Document generation (Word/Excel)
├── utils.py                                  # Helper functions
└── hook_formatter.py                         # Output formatting hook
```

---

## Core Functionalities

### 1. HARA Input Integration

**Tool: `load_hara_for_fsc`**
```python
@tool(return_direct=True)
def load_hara_for_fsc(tool_input, cat):
    """
    Load HARA outputs for FSC development.
    
    Sources (in priority order):
    1. Working memory (if chained from HARA plugin)
    2. hara_inputs/ folder (uploaded files)
    3. Generated documents from HARA plugin
    
    Extracts:
    - Safety Goals with ASILs
    - Hazardous events
    - Safe states
    - FTTIs
    - Operational situations
    
    Input: Item name or "use current HARA"
    Example: "load HARA for Battery Management System"
    """
```

**Parsing Logic:**
- Parse HARA table (Excel/CSV format)
- Extract safety goals with unique IDs
- Validate ASIL assignments
- Store in `cat.working_memory["fsc_safety_goals"]`

---

### 2. Safety Goal Refinement & Validation

**Tool: `refine_safety_goals`**
```python
@tool(return_direct=False)
def refine_safety_goals(tool_input, cat):
    """
    Refine preliminary safety goals into fully compliant technical goals.
    
    Per ISO 26262-4:2018, Clause 6.4.6:
    - Result-oriented (what state/outcome required)
    - Correct ASIL attached
    - Clear safe state specified
    - FTTI defined if time-critical
    - Measurable success criteria
    
    Input: Safety goal ID or "all goals"
    Example: "refine safety goal SG-001"
    """
```

**Refinement Checks:**
- Is goal result-oriented (not prescriptive)?
- Does it specify the required safe state?
- Is FTTI justified and realistic?
- Are verification criteria defined?
- Does it avoid implementation details?

---

### 3. Functional Safety Requirements (FSR) Derivation

**Tool: `derive_functional_safety_requirements`**
```python
@tool(return_direct=True)
def derive_functional_safety_requirements(tool_input, cat):
    """
    Transform safety goals into Functional Safety Requirements (FSRs).
    
    Uses "How to Achieve" decomposition:
    - Fault Detection requirements
    - Fault Reaction requirements
    - Fault Indication requirements
    
    Each FSR:
    - Inherits parent ASIL (or decomposed ASIL)
    - Has unique ID (FSR-XXX)
    - Is measurable and verifiable
    - Traces back to safety goal
    
    Input: Safety goal ID or "derive all FSRs"
    Example: "derive FSRs for SG-001"
    """
```

**Derivation Strategy:**
For each safety goal, generate:
1. **Detection FSRs**: How will faults be detected?
2. **Reaction FSRs**: How will safe state be achieved?
3. **Indication FSRs**: How will faults be communicated?

**Example:**
```
Safety Goal: "Prevent unintended battery discharge leading to loss of propulsion" (ASIL C)

FSR-001: Detect battery voltage deviation >5% from nominal (ASIL C)
FSR-002: Detect cell imbalance >200mV between any two cells (ASIL C)
FSR-003: Transition to safe state within 100ms of fault detection (ASIL C)
FSR-004: Communicate fault to driver via warning lamp within 200ms (ASIL B)
```

---

### 4. FSR Allocation & Functional Architecture

**Tool: `allocate_functional_requirements`**
```python
@tool(return_direct=True)
def allocate_functional_requirements(tool_input, cat):
    """
    Allocate FSRs to architectural elements.
    
    Allocation targets:
    - Hardware components (sensors, actuators, ECUs)
    - Software modules
    - Communication interfaces
    - External systems
    
    Creates allocation matrix:
    FSR ID | Allocated To | Interface Type | Rationale
    
    Input: FSR ID or "allocate all FSRs"
    Example: "allocate FSR-001 to voltage sensor"
    """
```

**Allocation Considerations:**
- Technical feasibility
- Performance requirements (timing, accuracy)
- Independence requirements (for redundancy)
- Communication bandwidth and latency
- Development complexity

**Tool: `define_functional_architecture`**
```python
@tool(return_direct=False)
def define_functional_architecture(tool_input, cat):
    """
    Define high-level architecture of safety functions.
    
    Describes:
    - Safety function blocks
    - Data flows between blocks
    - Internal vs external interfaces
    - Interaction with non-safety functions
    
    Input: Architecture description or "generate architecture"
    """
```

---

### 5. Technical Safety Requirements (TSR) Specification

**Tool: `derive_technical_safety_requirements`**
```python
@tool(return_direct=True)
def derive_technical_safety_requirements(tool_input, cat):
    """
    Refine FSRs into Technical Safety Requirements for the item.
    
    TSRs are more detailed and implementation-oriented:
    - Hardware requirements (voltage ranges, timing, diagnostics)
    - Software requirements (algorithms, data validation)
    - Environmental conditions
    - Verification criteria
    
    Input: FSR ID or "derive all TSRs"
    Example: "derive TSRs for FSR-001"
    """
```

**TSR Characteristics:**
- More specific than FSRs
- Include quantitative parameters
- Reference specific components/modules
- Define pass/fail criteria for verification

---

### 6. Safety Mechanism Identification

**Tool: `identify_safety_mechanisms`**
```python
@tool(return_direct=True)
def identify_safety_mechanisms(tool_input, cat):
    """
    Identify and describe safety mechanisms for FSRs/TSRs.
    
    Mechanism categories:
    - Diagnostic mechanisms (BIST, checksums, plausibility checks)
    - Redundancy (dual sensors, voting, lockstep cores)
    - Safe state management (shutdown sequences, degraded modes)
    - Watchdogs and supervision
    - Communication protection (CRC, sequence counters)
    
    Links mechanisms to requirements and calculates coverage.
    
    Input: Requirement ID or "identify all mechanisms"
    Example: "identify mechanisms for FSR-001"
    """
```

**Safety Mechanisms Catalog (from template):**
```json
{
  "diagnostic_mechanisms": [
    {
      "id": "SM_DIAG_001",
      "name": "Plausibility Check",
      "description": "Compare sensor reading against expected range",
      "applicable_to": ["voltage_sensor", "current_sensor", "temperature_sensor"],
      "diagnostic_coverage": "90-95%",
      "asil_suitability": ["A", "B", "C", "D"]
    },
    {
      "id": "SM_DIAG_002",
      "name": "Checksum Validation",
      "description": "Verify data integrity using CRC",
      "applicable_to": ["communication", "memory"],
      "diagnostic_coverage": "99%",
      "asil_suitability": ["B", "C", "D"]
    }
  ],
  "redundancy_mechanisms": [...],
  "safe_state_mechanisms": [...]
}
```

---

### 7. ASIL Tailoring & Decomposition

**Tool: `analyze_asil_decomposition`**
```python
@tool(return_direct=True)
def analyze_asil_decomposition(tool_input, cat):
    """
    Analyze if ASIL decomposition is beneficial for a requirement.
    
    Per ISO 26262-9:2018, Clause 5:
    - Assess independence requirements
    - Calculate decomposed ASILs
    - Verify freedom from interference
    - Document justification
    
    Valid decompositions:
    ASIL D = ASIL D(D) or ASIL B(D) + ASIL B(D)
    ASIL C = ASIL C(D) or ASIL B(D) + ASIL A(D)
    ASIL B = ASIL B(D) or ASIL A(D) + ASIL A(D)
    
    Input: Requirement ID
    Example: "analyze decomposition for FSR-003"
    """
```

**Tool: `apply_asil_decomposition`**
```python
@tool(return_direct=False)
def apply_asil_decomposition(tool_input, cat):
    """
    Apply ASIL decomposition to a requirement.
    
    Creates:
    - Two or more independent requirements
    - Assigns decomposed ASILs
    - Documents independence argument
    - Updates traceability
    
    Input: Requirement ID and decomposition strategy
    Example: "decompose FSR-003 into ASIL B + ASIL B"
    """
```

---

### 8. Traceability Management

**Automatic traceability linking:**
```
Safety Goal (SG-XXX)
  ├─> FSR-001 (Detection)
  │    ├─> TSR-001 (Hardware)
  │    ├─> TSR-002 (Software)
  │    └─> SM-001 (Mechanism)
  ├─> FSR-002 (Reaction)
  │    └─> TSR-003 (Safe state logic)
  └─> FSR-003 (Indication)
       └─> TSR-004 (HMI)
```

**Tool: `verify_traceability`**
```python
@tool(return_direct=True)
def verify_traceability(tool_input, cat):
    """
    Verify completeness of traceability links.
    
    Checks:
    - Every safety goal has FSRs
    - Every FSR is allocated
    - Every ASIL C/D FSR has safety mechanisms
    - No orphaned requirements
    
    Input: "verify traceability" or specific ID
    """
```

---

### 9. FSC Document Generation

**Tool: `generate_fsc_document`**
```python
@tool(return_direct=True)
def generate_fsc_document(tool_input, cat):
    """
    Generate complete FSC work product (Word + Excel).
    
    Document structure per ISO 26262-4:2018, Clause 7.5:
    1. Introduction
    2. Referenced Documents
    3. Terms and Abbreviations
    4. Safety Goals (summary)
    5. Functional Safety Requirements
    6. FSR Allocation Matrix
    7. Technical Safety Requirements (initial)
    8. Safety Mechanisms
    9. ASIL Decomposition (if applicable)
    10. Verification Strategy (outline)
    11. Traceability Matrix
    12. Approvals
    
    Input: "generate FSC document"
    """
```

**Output Files:**
- `[System]_FSC_[Date].docx` - Complete FSC document
- `[System]_FSC_Traceability_[Date].xlsx` - Traceability matrix
- Saved to: `generated_documents/05_FSC/`

---

### 10. Compliance Checkpoint & Guidance

**Tool: `check_fsc_compliance`**
```python
@tool(return_direct=True)
def check_fsc_compliance(tool_input, cat):
    """
    Check FSC completeness against ISO 26262-4 requirements.
    
    Verifies:
    - All safety goals addressed
    - FSRs are traceable and verifiable
    - ASIL D requirements have >99% diagnostic coverage
    - Safe states are defined
    - Verification methods are specified
    
    Input: "check compliance"
    """
```

**Compliance Checklist (from template):**
```json
{
  "items": [
    {
      "id": "FSC_CHECK_001",
      "category": "Requirements Derivation",
      "requirement": "All Safety Goals Decomposed",
      "description": "Each safety goal shall be refined into measurable FSRs",
      "iso_clause": "ISO 26262-4:2018, Clause 6.4.2"
    },
    {
      "id": "FSC_CHECK_002",
      "category": "ASIL Integrity",
      "requirement": "ASIL Inheritance",
      "description": "FSRs inherit parent safety goal ASIL unless decomposed",
      "iso_clause": "ISO 26262-9:2018, Clause 5"
    }
  ]
}
```

---

## Workflow Integration

### Sequential Flow (After HARA)
```
Item Definition → HARA → FSC → Technical Safety Concept
```

### FSC Development Steps

**Step 1: Load HARA**
```
User: "Load HARA for Battery Management System"
Tool: load_hara_for_fsc
Output: Safety goals summary
```

**Step 2: Refine Safety Goals (if needed)**
```
User: "Refine safety goal SG-003"
Tool: refine_safety_goals
Output: Refined goal with clear criteria
```

**Step 3: Derive FSRs**
```
User: "Derive functional safety requirements for all goals"
Tool: derive_functional_safety_requirements
Output: FSR table with traceability
```

**Step 4: Allocate FSRs**
```
User: "Allocate FSRs to architectural elements"
Tool: allocate_functional_requirements
Output: Allocation matrix
```

**Step 5: Specify TSRs**
```
User: "Derive technical safety requirements"
Tool: derive_technical_safety_requirements
Output: Detailed TSR specifications
```

**Step 6: Identify Safety Mechanisms**
```
User: "Identify safety mechanisms for all requirements"
Tool: identify_safety_mechanisms
Output: Mechanism catalog with coverage
```

**Step 7: Check ASIL Decomposition**
```
User: "Analyze ASIL decomposition opportunities"
Tool: analyze_asil_decomposition
Output: Decomposition recommendations
```

**Step 8: Generate FSC Document**
```
User: "Generate FSC document"
Tool: generate_fsc_document
Output: Complete FSC work product (Word + Excel)
```

---

## Key Data Structures

### Working Memory Keys
```python
cat.working_memory = {
    "fsc_safety_goals": [...],           # From HARA
    "fsc_functional_requirements": [...], # Derived FSRs
    "fsc_technical_requirements": [...],  # Derived TSRs
    "fsc_allocation_matrix": {...},       # FSR allocations
    "fsc_safety_mechanisms": [...],       # Identified mechanisms
    "fsc_asil_decompositions": [...],     # Decomposition records
    "fsc_traceability": {...},            # Complete trace links
    "fsc_stage": "requirements_derived",  # Workflow stage
    "system_name": "Battery Management System"
}
```

### FSR Structure
```json
{
  "id": "FSR-001",
  "parent_safety_goal": "SG-003",
  "description": "Detect battery voltage deviation >5% from nominal",
  "asil": "C",
  "type": "detection",
  "allocated_to": "Voltage Monitoring Module",
  "verification_method": "Unit Test + Integration Test",
  "traces_to": ["TSR-001", "TSR-002"],
  "safety_mechanisms": ["SM-DIAG-001", "SM-DIAG-005"]
}
```

---

## Output Document Structure

### FSC Document Template (Word)
```
1. Introduction
   - Purpose of FSC
   - Scope and boundaries
   - Referenced item definition and HARA

2. Safety Goals Overview
   - Summary table of all safety goals
   - ASIL distribution

3. Functional Safety Requirements
   3.1 Fault Detection Requirements
   3.2 Fault Reaction Requirements
   3.3 Fault Indication Requirements

4. FSR Allocation
   - Allocation matrix (FSR → Component)
   - Interface definitions

5. Technical Safety Requirements
   - Hardware TSRs
   - Software TSRs
   - Environmental requirements

6. Safety Mechanisms
   6.1 Diagnostic Mechanisms
   6.2 Redundancy and Diversity
   6.3 Safe State Management

7. ASIL Decomposition
   - Decomposition rationale
   - Independence justification

8. Verification Strategy
   - Requirements verification methods
   - Test coverage targets

9. Traceability Matrix
   - SG → FSR → TSR → SM links

10. Approvals
```

---

## ISO 26262-4:2018 Compliance Mapping

| FSC Tool Feature | ISO 26262-4 Clause | Work Product |
|------------------|-------------------|--------------|
| Safety Goal Refinement | 6.4.6 | Refined Safety Goals |
| FSR Derivation | 6.4.2, 6.4.3 | Functional Safety Requirements |
| FSR Allocation | 6.4.4 | Allocation Matrix |
| TSR Specification | 6.4.5 | Technical Safety Requirements |
| Safety Mechanisms | 6.4.5.4 | Safety Mechanism Catalog |
| ASIL Decomposition | Ref to Part 9, Clause 5 | Decomposition Justification |
| Traceability | 6.4.9 | Traceability Information |
| FSC Document | 7.5 | Functional Safety Concept |

---

## Dependencies

### Python Libraries
```
openpyxl>=3.1.0      # Excel file handling
python-docx>=0.8.11  # Word document generation
PyPDF2>=3.0.0        # PDF reading (optional)
```

### Plugin Dependencies
- **HARA Assistant**: Provides safety goals (can work standalone with manual input)
- **Item Definition Developer**: Provides system context (optional)
- **Output Formatter**: Automatic document generation

---

## Usage Examples

### Example 1: Complete FSC Development
```
User: Load HARA for Battery Management System
Assistant: [Loads 15 safety goals with ASILs B, C, D]

User: Derive functional safety requirements for all goals
Assistant: [Generates 45 FSRs across detection/reaction/indication]

User: Allocate FSRs to architectural elements
Assistant: [Creates allocation matrix for HW/SW components]

User: Identify safety mechanisms
Assistant: [Proposes plausibility checks, CRC, voting, watchdogs]

User: Generate FSC document
Assistant: [Creates complete FSC work product]
```

### Example 2: ASIL Decomposition
```
User: Analyze decomposition for FSR-023
Assistant: FSR-023 (ASIL D) is complex. Decomposition recommended:
- FSR-023A: Voltage plausibility (ASIL B)
- FSR-023B: Independent voltage backup (ASIL B)
Requires independence: separate power supply, different sensing principle

User: Apply decomposition
Assistant: [Updates FSR-023 with decomposed requirements]
```

---

## Next Steps for Implementation

1. **Phase 1 - Core Tools** (Weeks 1-2)
   - HARA input loading
   - FSR derivation
   - Basic traceability

2. **Phase 2 - Allocation & TSRs** (Weeks 3-4)
   - Allocation logic
   - TSR specification
   - Architecture definition

3. **Phase 3 - Safety Mechanisms** (Week 5)
   - Mechanism catalog
   - Coverage calculation
   - Mechanism-to-requirement linking

4. **Phase 4 - ASIL Decomposition** (Week 6)
   - Decomposition analysis
   - Independence verification
   - Decomposition application

5. **Phase 5 - Document Generation** (Weeks 7-8)
   - Word document formatter
   - Excel traceability matrix
   - Compliance checker
   - Integration testing

6. **Phase 6 - Testing & Validation** (Week 9)
   - End-to-end workflow testing
   - ISO 26262-4 compliance verification
   - Documentation review

---

## Success Criteria

✅ **Functional Completeness**
- All 10 core functionalities implemented
- Integration with HARA plugin working
- Document generation produces ISO-compliant outputs

✅ **ISO 26262 Compliance**
- All Clause 7.5 work product elements present
- Traceability from safety goals to mechanisms
- ASIL integrity maintained throughout

✅ **Usability**
- Clear workflow guidance
- Helpful error messages
- Professional document outputs

✅ **Quality**
- Comprehensive test coverage
- No critical bugs
- Performance acceptable (<5s per tool call)

---

## Contact & Support

**Author:** Tonino De Nigris  
**GitHub:** https://github.com/tondeni/AI_Agent-FSC_Developer  
**License:** [Your License]  
**ISO 26262 Edition:** 2018 (2nd Edition)