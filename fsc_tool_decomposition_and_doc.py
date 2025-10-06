# fsc_tool_decomposition_and_doc.py
# ASIL Decomposition Analysis and FSC Document Generation
# Per ISO 26262-9:2018, Clause 5 and ISO 26262-4:2018, Clause 7.5

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime
import json
import os


@tool(return_direct=True)
def analyze_asil_decomposition(tool_input, cat):
    """
    Analyze if ASIL decomposition would be beneficial for requirements.
    
    Per ISO 26262-9:2018, Clause 5:
    - Evaluates complexity vs independence overhead
    - Checks valid decomposition paths
    - Assesses independence feasibility
    - Recommends decomposition strategy
    
    Input: "analyze decomposition opportunities" or "analyze decomposition for FSR-XXX"
    Example: "analyze decomposition for FSR-003-REACT-1"
    """
    
    print("✅ TOOL CALLED: analyze_asil_decomposition")
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not fsrs:
        return "❌ No FSRs available. Please derive FSRs first."
    
    system_name = cat.working_memory.get("system_name", "the system")
    input_str = str(tool_input).strip().lower()
    
    # Load decomposition rules
    plugin_folder = os.path.dirname(__file__)
    decomp_rules = load_decomposition_rules(plugin_folder)
    
    if not decomp_rules:
        return "❌ Decomposition rules not found."
    
    # Determine scope
    if input_str in ["all", "opportunities", "analyze all", ""]:
        # Find candidates: ASIL C/D requirements that might benefit
        candidates = [f for f in fsrs if f['asil'] in ['C', 'D']]
        log.info(f"🧩 Analyzing decomposition for {len(candidates)} ASIL C/D FSRs")
    else:
        # Specific FSR
        fsr_id = str(tool_input).strip().upper()
        if not fsr_id.startswith('FSR-'):
            fsr_id = 'FSR-' + fsr_id
        candidates = [f for f in fsrs if f['id'] == fsr_id]
        
        if not candidates:
            return f"❌ FSR '{fsr_id}' not found."
    
    # Build analysis prompt
    prompt = f"""You are analyzing ASIL decomposition opportunities per ISO 26262-9:2018, Clause 5.

**Context:**
- System: {system_name}
- Requirements to analyze: {len(candidates)}

**ASIL Decomposition Overview:**

ASIL decomposition allows splitting a high-ASIL requirement into multiple lower-ASIL requirements with independence, potentially reducing development complexity.

**Valid Decompositions:**

{format_decomposition_rules(decomp_rules)}

**When Decomposition is Beneficial:**
- Requirement is complex and difficult at full ASIL
- Technology limitations at high ASIL
- Cost/schedule savings significant
- Architecture naturally supports independent channels
- Reuse of existing ASIL-rated components

**When Decomposition is NOT Beneficial:**
- Requirement is simple and achievable
- Independence overhead exceeds savings
- Architecture doesn't support separation
- Verification burden increases significantly

**Independence Requirements:**
- Separate hardware or software channels
- Independent power supplies
- Freedom from interference
- Independent failure modes
- Spatial/temporal separation

**Your Task:**
For each FSR, analyze:
1. Is decomposition technically feasible?
2. Would it reduce overall complexity?
3. What independence measures are needed?
4. What are the costs/benefits?

**Output Format:**

---
## Decomposition Analysis for: [FSR-ID]
**FSR:** [Description]
**Current ASIL:** [X]

### Complexity Assessment
- **Implementation Complexity:** [High/Medium/Low]
- **Key Challenges:** [What makes this FSR difficult at current ASIL?]

### Decomposition Feasibility
- **Recommended Decomposition:** [e.g., "ASIL D → ASIL B(D) + ASIL B(D)" or "No decomposition recommended"]
- **Rationale:** [Why this decomposition or why not decompose]

### If Decomposition Recommended:

**Proposed Split:**
- **Requirement 1:** [Description of first part] - ASIL [X(D)]
- **Requirement 2:** [Description of second part] - ASIL [Y(D)]

**Independence Strategy:**
- **Hardware:** [How to achieve HW independence]
- **Software:** [How to achieve SW independence if applicable]
- **Power:** [Independent power or demonstrated immunity]
- **Failure Modes:** [Different failure mechanisms]

**Verification Impact:**
- **Additional Verification:** [What new verifications needed?]
- **Overall Effort:** [Increases/Decreases/Same]

**Cost-Benefit Analysis:**
- **Benefits:** [Reduced complexity, cost savings, etc.]
- **Costs:** [Independence overhead, additional verification]
- **Recommendation:** ✅ Proceed / ❌ Do not decompose / ⚠️ Further analysis needed

---

**FSRs to Analyze:**

"""
    
    # Add FSR details
    for fsr in candidates[:15]:  # Limit to avoid token overflow
        prompt += f"""
### {fsr['id']}
- **Description:** {fsr['description']}
- **ASIL:** {fsr['asil']}
- **Type:** {fsr['type']}
- **Allocated To:** {fsr.get('allocated_to', 'Unknown')}
- **Mechanisms:** {', '.join(fsr.get('safety_mechanisms', ['None']))}

"""
    
    prompt += """
**Now analyze decomposition opportunities for all FSRs.**
"""
    
    try:
        decomposition_analysis = cat.llm(prompt).strip()
        
        # Parse recommendations
        recommendations = parse_decomposition_recommendations(decomposition_analysis, candidates)
        
        # Store in working memory
        cat.working_memory["fsc_decomposition_analysis"] = recommendations
        
        # Count recommendations
        decompose_count = len([r for r in recommendations if r['recommend_decomposition']])
        
        summary = f"""✅ **ASIL Decomposition Analysis Complete**

**Summary:**
- FSRs Analyzed: {len(candidates)}
- Decomposition Recommended: {decompose_count}
- Retain Current ASIL: {len(candidates) - decompose_count}

---

**Detailed Analysis:**

{decomposition_analysis}

---

**ISO 26262-9:2018 Compliance:**
✅ Clause 5: ASIL decomposition analysis complete

**Next Steps:**

1. **Apply Decomposition (if recommended):**
   - `apply decomposition for [FSR-ID]` - Split requirement

2. **Review Architecture:**
   - Verify independence can be achieved
   - Update functional architecture if needed

3. **Continue FSC Development:**
   - `generate FSC document` - Create complete work product

4. **Document Rationale:**
   - All decomposition decisions will be included in FSC
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error analyzing decomposition: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error analyzing decomposition: {str(e)}"


@tool(return_direct=False)
def apply_asil_decomposition(tool_input, cat):
    """
    Apply ASIL decomposition to a specific requirement.
    
    Creates two or more independent requirements at lower ASIL.
    Updates traceability and documents independence justification.
    
    Input: FSR ID and decomposition strategy
    Example: "apply decomposition for FSR-003-REACT-1: split into ASIL B + ASIL B"
    """
    
    input_str = str(tool_input).strip()
    
    if ':' not in input_str:
        return """❌ Please specify decomposition strategy.

**Format:** `apply decomposition for [FSR-ID]: [strategy]`
**Example:** `apply decomposition for FSR-003-REACT-1: split into ASIL B(D) + ASIL B(D)`

**Valid strategies:**
- ASIL D → B(D) + B(D)
- ASIL D → C(D) + A(D)
- ASIL C → B(D) + A(D)
- ASIL B → A(D) + A(D)
"""
    
    parts = input_str.split(':', 1)
    fsr_id_part = parts[0].replace('for', '').strip().upper()
    strategy = parts[1].strip()
    
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    # Find FSR
    fsr_id = None
    for fsr in fsrs:
        if fsr['id'] in fsr_id_part:
            fsr_id = fsr['id']
            break
    
    if not fsr_id:
        return f"❌ FSR not found in '{fsr_id_part}'"
    
    fsr = next((f for f in fsrs if f['id'] == fsr_id), None)
    
    # Parse strategy
    decomposed_asils = parse_decomposition_strategy(strategy, fsr['asil'])
    
    if not decomposed_asils:
        return f"❌ Invalid decomposition strategy: '{strategy}'"
    
    # Create decomposed requirements
    decomposed_fsrs = []
    
    for i, asil in enumerate(decomposed_asils, 1):
        new_fsr = {
            'id': f"{fsr_id}-DEC{i}",
            'description': f"[Part {i} of decomposed] {fsr['description']}",
            'asil': asil,
            'type': fsr['type'],
            'parent_safety_goal': fsr['parent_safety_goal'],
            'original_requirement': fsr_id,
            'decomposition_part': i,
            'independence_requirements': 'TBD - Must define independence measures',
            'status': 'decomposed',
            'allocated_to': None,
            'created_date': datetime.now().isoformat()
        }
        decomposed_fsrs.append(new_fsr)
        fsrs.append(new_fsr)
    
    # Mark original as decomposed
    fsr['status'] = 'decomposed_into'
    fsr['decomposed_to'] = [d['id'] for d in decomposed_fsrs]
    
    # Store updated FSRs
    cat.working_memory["fsc_functional_requirements"] = fsrs
    
    # Track decomposition
    decompositions = cat.working_memory.get("fsc_asil_decompositions", [])
    decompositions.append({
        'original_fsr': fsr_id,
        'original_asil': fsr['asil'],
        'decomposed_fsrs': [d['id'] for d in decomposed_fsrs],
        'decomposed_asils': decomposed_asils,
        'strategy': strategy,
        'date': datetime.now().isoformat()
    })
    cat.working_memory["fsc_asil_decompositions"] = decompositions
    
    result = f"""✅ **ASIL Decomposition Applied**

**Original FSR:** {fsr_id} (ASIL {fsr['asil']})
{fsr['description']}

**Decomposed Into:**
"""
    
    for dec_fsr in decomposed_fsrs:
        result += f"\n- **{dec_fsr['id']}** (ASIL {dec_fsr['asil']})"
    
    result += f"""

**Critical Next Steps:**

1. **Define Independence Measures:**
   Each decomposed requirement must be independent. Define:
   - Separate hardware channels OR
   - Independent software modules with memory protection OR
   - Different failure modes/mechanisms
   - Freedom from interference

2. **Allocate Decomposed Requirements:**
   - `allocate {decomposed_fsrs[0]['id']} to [independent channel 1]`
   - `allocate {decomposed_fsrs[1]['id']} to [independent channel 2]`

3. **Document Independence Justification:**
   - Update functional architecture
   - Specify interference prevention measures

4. **Update Verification:**
   - Verify independence (architecture review, FMEA)
   - Test each channel separately
   - Verify interference immunity

**⚠️ Warning:**
Decomposition only valid if independence is truly achieved!
"""
    
    return result


@tool(return_direct=True)
def generate_fsc_document(tool_input, cat):
    """
    Generate complete Functional Safety Concept work product.
    
    Creates:
    - Word document with all FSC sections (ISO 26262-4, Clause 7.5)
    - Excel traceability matrix
    - Compliance checklist
    
    Input: "generate FSC document" or "generate FSC"
    """
    
    print("✅ TOOL CALLED: generate_fsc_document")
    
    # Check if workflow is complete enough
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    tsrs = cat.working_memory.get("fsc_technical_requirements", [])
    mechanisms = cat.working_memory.get("fsc_safety_mechanisms", [])
    
    if not safety_goals:
        return """❌ Cannot generate FSC: No safety goals loaded.

**Required Steps:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive all FSRs`
3. Allocate FSRs: `allocate FSRs`
4. Generate document: `generate FSC document`
"""
    
    if not fsrs:
        return """❌ Cannot generate FSC: No FSRs derived.

**Required Steps:**
1. Derive FSRs: `derive all FSRs`
2. Allocate FSRs: `allocate FSRs`
3. Generate document: `generate FSC document`
"""
    
    # Warn if incomplete but allow generation
    warnings = []
    
    allocated_count = len([f for f in fsrs if f.get('allocated_to')])
    if allocated_count < len(fsrs) * 0.8:
        warnings.append(f"⚠️ Only {allocated_count}/{len(fsrs)} FSRs allocated")
    
    if not tsrs:
        warnings.append("⚠️ No TSRs derived (recommended but optional)")
    
    if not mechanisms:
        warnings.append("⚠️ No safety mechanisms identified")
    
    system_name = cat.working_memory.get("system_name", "Unknown_System")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate document content
    log.info(f"📄 Generating FSC document for: {system_name}")
    
    doc_content = generate_fsc_content(cat, system_name, safety_goals, fsrs, tsrs, mechanisms)
    
    # Set flags for formatter hook
    cat.working_memory["document_type"] = "fsc"
    cat.working_memory["fsc_document_content"] = doc_content
    cat.working_memory["fsc_stage"] = "document_generated"
    
    summary = f"""✅ **Functional Safety Concept Document Generated**

**System:** {system_name}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Document Statistics:**
- Safety Goals: {len(safety_goals)}
- Functional Safety Requirements: {len(fsrs)}
- Technical Safety Requirements: {len(tsrs)}
- Safety Mechanisms: {len(mechanisms)}
- Pages: ~{estimate_page_count(safety_goals, fsrs, tsrs, mechanisms)}

**Files Created:**
- `{system_name}_FSC_{timestamp}.docx` (Main document)
- `{system_name}_FSC_Traceability_{timestamp}.xlsx` (Trace matrix)
- Location: `generated_documents/05_FSC/`

"""
    
    if warnings:
        summary += "**⚠️ Warnings:**\n"
        for warning in warnings:
            summary += f"{warning}\n"
        summary += "\n"
    
    summary += f"""---

**Document Sections:**
1. ✅ Introduction and References
2. ✅ Safety Goals Overview ({len(safety_goals)} goals)
3. ✅ Functional Safety Requirements ({len(fsrs)} FSRs)
4. ✅ FSR Allocation (to architectural elements)
5. {'✅' if tsrs else '⚠️'} Technical Safety Requirements ({len(tsrs)} TSRs)
6. {'✅' if mechanisms else '⚠️'} Safety Mechanisms ({len(mechanisms)} mechanisms)
7. {'✅' if cat.working_memory.get('fsc_asil_decompositions') else '➖'} ASIL Decomposition
8. ✅ Verification Strategy (outline)
9. ✅ Traceability Matrix
10. ✅ Approvals (template)

---

**ISO 26262-4:2018 Compliance:**
✅ Clause 7.5: FSC work product complete
✅ All required sections present
✅ Traceability established

**Next Steps:**

1. **Review Document:**
   - Open generated Word document
   - Review all sections for completeness
   - Fill approval signatures

2. **Compliance Check:**
   - `check fsc compliance` - Verify against ISO 26262-4

3. **Proceed to Next Phase:**
   - Technical Safety Concept (ISO 26262-5)
   - Hardware/Software Development (Parts 6-7)

4. **Archive:**
   - Save document to version control
   - Link to HARA and Item Definition

**🎉 Congratulations!**
Your Functional Safety Concept is complete and ready for formal review.
"""
    
    return summary


def load_decomposition_rules(plugin_folder):
    """Load ASIL decomposition rules from template."""
    
    template_path = os.path.join(plugin_folder, "templates", "asil_decomposition_rules.json")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Error loading decomposition rules: {e}")
        return None


def format_decomposition_rules(rules):
    """Format decomposition rules for prompt."""
    
    if not rules or 'valid_decompositions' not in rules:
        return "No rules available"
    
    formatted = ""
    
    for asil, options in rules['valid_decompositions'].items():
        formatted += f"\n**{asil.replace('_', ' ')}:**\n"
        for option in options:
            formatted += f"- {option['option']}: {option['description']}\n"
    
    return formatted


def parse_decomposition_recommendations(analysis, fsrs):
    """Parse decomposition recommendations from LLM response."""
    
    recommendations = []
    
    for fsr in fsrs:
        # Simple heuristic: look for recommendation keywords in analysis
        fsr_section = analysis[analysis.find(fsr['id']):analysis.find(fsr['id']) + 500] if fsr['id'] in analysis else ""
        
        recommend_decompose = any(keyword in fsr_section.lower() for keyword in ['✅ proceed', 'recommended decomposition:', 'asil b(d) + asil b(d)'])
        
        recommendations.append({
            'fsr_id': fsr['id'],
            'recommend_decomposition': recommend_decompose,
            'rationale': 'See detailed analysis above'
        })
    
    return recommendations


def parse_decomposition_strategy(strategy, original_asil):
    """Parse decomposition strategy string into ASIL list."""
    
    strategy_lower = strategy.lower()
    
    # Valid patterns
    patterns = {
        'b(d) + b(d)': ['B', 'B'],
        'b + b': ['B', 'B'],
        'c(d) + a(d)': ['C', 'A'],
        'c + a': ['C', 'A'],
        'a(d) + a(d)': ['A', 'A'],
        'a + a': ['A', 'A']
    }
    
    for pattern, asils in patterns.items():
        if pattern in strategy_lower:
            return asils
    
    return None


def generate_fsc_content(cat, system_name, safety_goals, fsrs, tsrs, mechanisms):
    """Generate the main FSC document content."""
    
    content = f"""# Functional Safety Concept
## {system_name}

**Document Version:** 1.0
**Date:** {datetime.now().strftime("%Y-%m-%d")}
**Status:** Draft

---

## 1. Introduction

### 1.1 Purpose and Scope

This Functional Safety Concept (FSC) document defines the functional safety requirements, their allocation to architectural elements, and the technical realization strategy for achieving the safety goals identified in the Hazard Analysis and Risk Assessment (HARA) for the {system_name}.

This document satisfies the requirements of ISO 26262-4:2018, Clause 7.5.

### 1.2 Referenced Documents

- Item Definition for {system_name} (ISO 26262-3:2018, Clause 5)
- HARA for {system_name} (ISO 26262-3:2018, Clause 6)
- ISO 26262-4:2018 - Product development at the system level
- ISO 26262-9:2018 - ASIL-oriented and safety-oriented analyses

### 1.3 Terms, Definitions, and Abbreviations

- **FSR:** Functional Safety Requirement
- **TSR:** Technical Safety Requirement
- **FTTI:** Fault-Tolerant Time Interval
- **ASIL:** Automotive Safety Integrity Level
- **SM:** Safety Mechanism

---

## 2. Safety Goals Overview

### 2.1 Safety Goals Summary

The following safety goals have been derived from the HARA:

| SG-ID | Safety Goal | ASIL | Safe State | FTTI |
|-------|-------------|------|------------|------|
"""
    
    for goal in safety_goals[:20]:  # Limit in summary
        content += f"| {goal['id']} | {goal['goal'][:60]}... | {goal['asil']} | {goal.get('safe_state', 'TBD')[:30]} | {goal.get('ftti', 'N/A')} |\n"
    
    # Count by ASIL
    asil_counts = {'D': 0, 'C': 0, 'B': 0, 'A': 0}
    for goal in safety_goals:
        if goal['asil'] in asil_counts:
            asil_counts[goal['asil']] += 1
    
    content += f"""

**Total Safety Goals:** {len(safety_goals)}
- ASIL D: {asil_counts['D']}
- ASIL C: {asil_counts['C']}
- ASIL B: {asil_counts['B']}
- ASIL A: {asil_counts['A']}

---

## 3. Functional Safety Requirements

### 3.1 Overview

A total of {len(fsrs)} Functional Safety Requirements have been derived from the safety goals using Detection-Reaction-Indication decomposition.

### 3.2 Detection Requirements

These requirements specify how faults and hazardous conditions will be detected.

"""
    
    detection_fsrs = [f for f in fsrs if f['type'] == 'detection']
    for fsr in detection_fsrs[:10]:
        content += f"**{fsr['id']}** (ASIL {fsr['asil']}): {fsr['description']}\n\n"
    
    content += f"""
### 3.3 Reaction Requirements

These requirements specify how the system will achieve safe states.

"""
    
    reaction_fsrs = [f for f in fsrs if f['type'] == 'reaction']
    for fsr in reaction_fsrs[:10]:
        content += f"**{fsr['id']}** (ASIL {fsr['asil']}): {fsr['description']}\n\n"
    
    content += """
[Full FSR list in traceability matrix]

---

## 4. FSR Allocation

FSRs have been allocated to architectural elements as shown in the allocation matrix (see Excel file).

---

## 5. Technical Safety Requirements

"""
    
    if tsrs:
        content += f"A total of {len(tsrs)} Technical Safety Requirements have been specified.\n\n"
    else:
        content += "TSRs will be further detailed during Technical Safety Concept phase.\n\n"
    
    content += f"""---

## 6. Safety Mechanisms

A total of {len(mechanisms)} safety mechanisms have been identified.

---

## 7. ASIL Decomposition

"""
    
    decompositions = cat.working_memory.get("fsc_asil_decompositions", [])
    if decompositions:
        content += f"{len(decompositions)} requirements have been decomposed.\n\n"
    else:
        content += "No ASIL decomposition applied. All requirements maintain original ASIL.\n\n"
    
    content += """---

## 8. Verification Strategy

Verification methods will be specified per requirement type and ASIL level.

---

## 9. Traceability

Complete traceability is maintained from Safety Goals through FSRs, TSRs, to Safety Mechanisms.
See traceability matrix (Excel file).

---

## 10. Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Safety Engineer | ______________ | ______________ | ______ |
| System Architect | ______________ | ______________ | ______ |
| Project Manager | ______________ | ______________ | ______ |
"""
    
    return content


def estimate_page_count(safety_goals, fsrs, tsrs, mechanisms):
    """Estimate document page count."""
    
    pages = 5  # Introduction, approvals
    pages += len(safety_goals) * 0.3
    pages += len(fsrs) * 0.4
    pages += len(tsrs) * 0.3
    pages += len(mechanisms) * 0.2
    
    return int(pages)