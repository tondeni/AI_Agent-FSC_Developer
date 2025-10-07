# fsc_tool_validation_verification.py
# Safety Validation Criteria and FSC Verification Tools
# Per ISO 26262-3:2018, Clauses 7.4.3 and 7.4.4

from cat.mad_hatter.decorators import tool
from cat.log import log
from datetime import datetime


@tool(return_direct=True)
def specify_safety_validation_criteria(tool_input, cat):
    """
    Specify acceptance criteria for safety validation of the item.
    
    Per ISO 26262-3:2018, 7.4.3.1:
    The acceptance criteria for safety validation of the item shall be specified
    based on the functional safety requirements and the safety goals.
    
    NOTE 1: For further requirements on detailing the criteria and list of 
    characteristics to be validated (see ISO 26262-4:2018, Clause 8).
    
    NOTE 2: Safety validation of safety goals is addressed on upper right of V cycle
    but is included in activities during development and not only performed at the end.
    
    Input: "specify validation criteria" or "validation criteria for FSR-XXX"
    Example: "specify validation criteria"
    """
    
    print("✅ TOOL CALLED: specify_safety_validation_criteria")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    
    if not safety_goals:
        return """❌ No safety goals loaded.

**Required per ISO 26262-3:2018, 7.4.3.1:**
Acceptance criteria for safety validation shall be specified based on:
- Functional safety requirements
- Safety goals

**Steps:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive FSRs for all goals`
3. Specify validation criteria: `specify validation criteria`
"""
    
    if not fsrs:
        return """❌ No FSRs derived yet.

**Required:**
1. Derive FSRs: `derive FSRs for all goals`
2. Then specify validation criteria: `specify validation criteria`
"""
    
    system_name = cat.working_memory.get("system_name", "the system")
    
    log.info(f"📋 Specifying safety validation criteria for {system_name}")
    
    # Build validation criteria specification prompt
    prompt = f"""You are specifying Safety Validation Criteria per ISO 26262-3:2018, Clause 7.4.3.

**System:** {system_name}
**Safety Goals:** {len(safety_goals)}
**FSRs:** {len(fsrs)}

**ISO 26262-3:2018, 7.4.3.1 Requirement:**
The acceptance criteria for safety validation of the item shall be specified based on
the functional safety requirements and the safety goals.

**Your Task:**
For each safety goal and its associated FSRs, specify measurable acceptance criteria
that will be used during safety validation (ISO 26262-4:2018, Clause 8).

**Validation Criteria Structure:**

For each Safety Goal:

1. **Goal-Level Acceptance Criteria**
   - How to validate the safety goal is achieved
   - Overall system behavior validation
   - Integration with vehicle-level validation

2. **FSR-Level Acceptance Criteria**
   - For each FSR, define acceptance criteria
   - Measurable pass/fail criteria
   - Test methods and conditions
   - Success criteria

3. **Characteristics to be Validated** (per ISO 26262-4:2018, Clause 8)
   - Functional behavior (nominal and degraded)
   - Fault detection capability
   - Safe state transitions
   - Timing performance (FTTI compliance)
   - Warning/indication effectiveness
   - Driver controllability
   - Fault tolerance behavior
   - Arbitration logic (if applicable)

**Output Format:**

---
## Safety Validation Criteria for SG: [SG-ID]
**Safety Goal:** [Description]
**ASIL:** [X]

### Goal-Level Acceptance Criteria

**VC-[SG-ID]-GOAL**
**Criterion:** The system shall [measurable criterion for safety goal achievement]
**Validation Method:** [Test, Analysis, Inspection, Review]
**Test Conditions:**
- [Operating conditions]
- [Environmental conditions]
- [Fault injection scenarios]

**Success Criteria:**
- [Quantifiable pass criteria]
- [Acceptable ranges/thresholds]

**Evidence Required:**
- [Test reports]
- [Analysis results]
- [Validation documentation]

### FSR-Level Acceptance Criteria

**VC-FSR-[FSR-ID]**
**FSR:** [FSR description]
**Type:** [Detection/Control/Transition/etc.]

**Criterion:** [Specific, measurable acceptance criterion]

**Validation Method:** 
- [Test type: unit, integration, vehicle-level]
- [Analysis type: if applicable]
- [Inspection: if applicable]

**Test Conditions:**
- Normal operation
- Degraded operation
- Fault conditions: [specific faults to inject]
- Operating modes: [all applicable modes]

**Success Criteria:**
- [Quantitative criteria with thresholds]
- [Timing requirements (if applicable)]
- [Accuracy requirements (if applicable)]
- [Coverage requirements (if applicable)]

**Traceability:**
- Linked to: [FSR-ID]
- Validates: [Safety Goal SG-ID]
- ASIL: [Inherited ASIL]

### Validation Characteristics per ISO 26262-4:2018, Clause 8

**Functional Behavior:**
- Nominal behavior validation
- Degraded functionality validation
- Limp-home mode validation (if applicable)

**Fault Detection:**
- Detection coverage validation
- Detection time validation (≤ FTTI)
- False positive rate validation

**Safe State Transitions:**
- Transition timing validation (≤ FTTI)
- Safe state maintenance validation
- Recovery validation (if applicable)

**Timing Performance:**
- FTTI compliance validation
- Fault handling time interval validation
- Response time validation

**Warnings/Indications:**
- Warning presentation validation
- Driver perception validation
- Controllability improvement validation

**Fault Tolerance:**
- Redundancy validation
- Degradation behavior validation
- Fail-operational capability validation (if applicable)

---

**Safety Goals and FSRs:**

"""
    
    for sg in safety_goals:
        prompt += f"""
### {sg['id']}
- **Safety Goal:** {sg['description']}
- **ASIL:** {sg['asil']}
- **Safe State:** {sg.get('safe_state', 'Not specified')}
- **FTTI:** {sg.get('ftti', 'TBD')}

**Associated FSRs:**
"""
        
        sg_fsrs = [f for f in fsrs if f.get('safety_goal_id') == sg['id']]
        for fsr in sg_fsrs[:5]:  # Show first 5
            prompt += f"""   - {fsr['id']}: {fsr.get('type', 'Unknown')} - {fsr.get('description', 'N/A')[:60]}
"""
        
        if len(sg_fsrs) > 5:
            prompt += f"   - ... and {len(sg_fsrs) - 5} more FSRs\n"
        
        prompt += "\n"
    
    prompt += """
**Requirements:**
- Criteria must be measurable and testable
- Include both qualitative and quantitative criteria
- Specify test conditions and success criteria
- Consider all operating modes and fault conditions
- Align with ASIL requirements
- Support safety validation per ISO 26262-4:2018, Clause 8

**Now specify safety validation criteria per ISO 26262-3:2018, 7.4.3 for all safety goals and FSRs.**
"""
    
    try:
        validation_analysis = cat.llm(prompt).strip()
        
        # Parse validation criteria
        validation_criteria = parse_validation_criteria(validation_analysis, safety_goals, fsrs)
        
        # Store in working memory
        cat.working_memory["fsc_validation_criteria"] = validation_criteria
        cat.working_memory["fsc_stage"] = "validation_criteria_specified"
        
        # Generate summary
        summary = f"""✅ **Safety Validation Criteria Specified**
*ISO 26262-3:2018, Clause 7.4.3 compliance*

**System:** {system_name}
**Validation Criteria Defined:** {len(validation_criteria)}

**Criteria Coverage:**
- Goal-Level Criteria: {len([vc for vc in validation_criteria if 'GOAL' in vc.get('id', '')])}
- FSR-Level Criteria: {len([vc for vc in validation_criteria if 'FSR' in vc.get('id', '')])}

**Validation Methods:**
"""
        
        methods = {}
        for vc in validation_criteria:
            method = vc.get('validation_method', 'Unknown')
            methods[method] = methods.get(method, 0) + 1
        
        for method, count in sorted(methods.items()):
            summary += f"- {method}: {count} criteria\n"
        
        summary += f"""

**Characteristics to be Validated:**
✅ Functional behavior (nominal and degraded)
✅ Fault detection capability
✅ Safe state transitions
✅ Timing performance (FTTI)
✅ Warning/indication effectiveness
✅ Fault tolerance behavior

---

**Detailed Validation Criteria:**

{validation_analysis}

---

**ISO 26262-3:2018, 7.4.3.1 Compliance:**
✅ Acceptance criteria specified based on FSRs and safety goals
✅ Criteria support safety validation per ISO 26262-4:2018, Clause 8

**Next Steps:**

1. **Verify FSC (7.4.4):**
   `verify FSC`
   
2. **Generate FSC Document (7.5):**
   `generate FSC document`
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error specifying validation criteria: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error specifying validation criteria: {str(e)}"


@tool(return_direct=True)
def verify_functional_safety_concept(tool_input, cat):
    """
    Verify the Functional Safety Concept.
    
    Per ISO 26262-3:2018, 7.4.4.1:
    The functional safety concept shall be verified in accordance with 
    ISO 26262-8:2018, Clause 9, to provide evidence for:
    
    a) its consistency and compliance with the safety goals; and
    b) its ability to mitigate or avoid the hazards.
    
    NOTE 1: Verification of ability to mitigate or avoid hazard can be carried
    out during concept phase to evaluate safety concept and indicate where 
    concept improvements are needed.
    
    NOTE 3: For verification, a traceability based argument can be used, i.e.
    the item complies with safety goals if item complies with FSRs.
    
    Input: "verify FSC" or "verify FSC compliance"
    """
    
    print("✅ TOOL CALLED: verify_functional_safety_concept")
    
    safety_goals = cat.working_memory.get("fsc_safety_goals", [])
    fsrs = cat.working_memory.get("fsc_functional_requirements", [])
    validation_criteria = cat.working_memory.get("fsc_validation_criteria", [])
    
    if not safety_goals or not fsrs:
        return """❌ Cannot verify FSC: Incomplete FSC development.

**Required per ISO 26262-3:2018, 7.4.4:**
1. Safety goals loaded
2. FSRs derived
3. FSRs allocated

**Steps:**
1. Load HARA: `load HARA for [item]`
2. Derive FSRs: `derive FSRs for all goals`
3. Allocate FSRs: `allocate all FSRs`
4. Verify FSC: `verify FSC`
"""
    
    system_name = cat.working_memory.get("system_name", "the system")
    
    log.info(f"✅ Verifying FSC for {system_name}")
    
    # Build verification prompt
    prompt = f"""You are verifying the Functional Safety Concept per ISO 26262-3:2018, Clause 7.4.4.

**System:** {system_name}
**Safety Goals:** {len(safety_goals)}
**FSRs:** {len(fsrs)}

**ISO 26262-3:2018, 7.4.4.1 Requirements:**

The FSC shall be verified per ISO 26262-8:2018, Clause 9, to provide evidence for:

a) **Consistency and Compliance with Safety Goals**
   - All safety goals addressed by FSRs
   - FSRs are consistent with safety goal intent
   - No contradictions or gaps
   - ASIL integrity maintained

b) **Ability to Mitigate or Avoid Hazards**
   - FSRs effectively address hazards
   - Strategies are feasible and effective
   - Safe states can be achieved within FTTI
   - Fault detection and control are adequate
   - Warnings are effective

**NOTE 3 from standard:** Traceability-based argument can be used:
"The item complies with safety goals if item complies with FSRs"

**Verification Checks:**

### 1. Completeness Verification

**Check 1.1: Safety Goal Coverage**
For each safety goal:
- ✅/❌ At least one FSR derived (per 7.4.2.2)
- ✅/❌ All aspects of safety goal addressed
- ✅/❌ Safe state specified (per 7.4.2.5)
- ✅/❌ FTTI considerations included

**Check 1.2: FSR Completeness**
For each FSR:
- ✅/❌ Clearly specified per ISO 26262-8
- ✅/❌ Measurable and verifiable
- ✅/❌ Operating modes considered (per 7.4.2.4.a)
- ✅/❌ FTTI considered (per 7.4.2.4.b)
- ✅/❌ Safe states considered (per 7.4.2.4.c)
- ✅/❌ Allocated to architectural element (per 7.4.2.8)

### 2. Consistency Verification

**Check 2.1: ASIL Consistency**
- ✅/❌ All FSRs inherit correct ASIL from safety goal (per 7.4.2.8.a)
- ✅/❌ No ASIL downgrade without decomposition
- ✅/❌ ASIL decomposition applied correctly (if applicable)

**Check 2.2: Traceability Consistency**
- ✅/❌ All FSRs linked to safety goals
- ✅/❌ No orphaned FSRs
- ✅/❌ Traceability is bidirectional

**Check 2.3: Timing Consistency**
- ✅/❌ Detection time + Reaction time ≤ FTTI
- ✅/❌ Fault handling time interval specified (per 7.4.2.3.h)
- ✅/❌ Emergency operation specified if needed (per 7.4.2.6)

### 3. Strategy Effectiveness Verification

**Check 3.1: Fault Detection Strategy (per 7.4.2.3.b)**
- ✅/❌ Detection mechanisms adequate for faults
- ✅/❌ Detection coverage sufficient for ASIL
- ✅/❌ Detection time supports FTTI

**Check 3.2: Safe State Transition Strategy (per 7.4.2.3.c)**
- ✅/❌ Safe state achievable within FTTI
- ✅/❌ Safe state prevents safety goal violation
- ✅/❌ Transition path is clearly defined

**Check 3.3: Warning Strategy (per 7.4.2.3.f,g)**
- ✅/❌ Warnings reduce exposure time (f)
- ✅/❌ Warnings increase controllability (g)
- ✅/❌ Driver actions specified (per 7.4.2.7)

**Check 3.4: Fault Tolerance Strategy (per 7.4.2.3.d)**
- ✅/❌ Redundancy adequate for ASIL (if applicable)
- ✅/❌ Degradation behavior acceptable
- ✅/❌ Functional redundancies specified (per 7.4.2.4.e)

### 4. Allocation Verification

**Check 4.1: Allocation Completeness**
- ✅/❌ All FSRs allocated to elements
- ✅/❌ Allocations are feasible
- ✅/❌ Allocation rationale provided

**Check 4.2: Freedom from Interference**
- ✅/❌ Interference considered (per 7.4.2.8.b)
- ✅/❌ Highest ASIL applied where needed
- ✅/❌ Interface specifications adequate

### 5. Validation Criteria Verification

**Check 5.1: Validation Criteria Adequacy**
- ✅/❌ Acceptance criteria specified (per 7.4.3.1)
- ✅/❌ Criteria are measurable
- ✅/❌ Criteria support safety validation

**Output Format:**

---
## FSC Verification Report
**System:** {system_name}
**Verification Date:** [Date]
**Verified per:** ISO 26262-3:2018, 7.4.4 and ISO 26262-8:2018, Clause 9

### Executive Summary
[Overall compliance status - PASS/FAIL/PASS WITH OBSERVATIONS]

### 1. Completeness Verification Results

#### 1.1 Safety Goal Coverage
[For each safety goal, check results]

SG-XXX: ✅ PASS / ❌ FAIL / ⚠️ OBSERVATION
- Check 1.1.1: [Result]
- Check 1.1.2: [Result]
...

#### 1.2 FSR Completeness
[Summary of FSR checks]
- Total FSRs: [count]
- Complete FSRs: [count]
- Incomplete FSRs: [count]

Issues found: [list if any]

### 2. Consistency Verification Results

#### 2.1 ASIL Consistency
[Results of ASIL checks]
Issues: [if any]

#### 2.2 Traceability Consistency
[Traceability verification results]
- All FSRs traceable to SGs: ✅/❌
- Bidirectional traceability: ✅/❌
Issues: [if any]

#### 2.3 Timing Consistency
[Timing verification results]
Issues: [if any]

### 3. Strategy Effectiveness Verification Results

[For each strategy type from 7.4.2.3]

Issues: [if any]
Recommendations: [if any]

### 4. Allocation Verification Results

[Allocation check results]

Issues: [if any]

### 5. Validation Criteria Verification Results

[Validation criteria adequacy]

Issues: [if any]

### 6. Overall Verification Conclusion

**Compliance Status:** [PASS / FAIL / PASS WITH OBSERVATIONS]

**Evidence for 7.4.4.1.a - Consistency and Compliance:**
[Summary of evidence]

**Evidence for 7.4.4.1.b - Ability to Mitigate/Avoid Hazards:**
[Summary of evidence]

**Traceability-Based Argument (NOTE 3):**
[Argument that item compliance with FSRs implies SG compliance]

### 7. Issues and Corrective Actions

**Critical Issues:** [count]
[List critical issues requiring correction]

**Observations:** [count]
[List observations for improvement]

**Recommendations:**
[Recommended improvements]

### 8. Verification Sign-Off

**Verified by:** [Name/Role]
**Review by:** [Name/Role]
**Approval:** [Name/Role]
**Date:** [Date]

---

**Now perform comprehensive FSC verification per ISO 26262-3:2018, 7.4.4.**

**Safety Goals:**
"""
    
    for sg in safety_goals:
        sg_fsrs = [f for f in fsrs if f.get('safety_goal_id') == sg['id']]
        prompt += f"""
{sg['id']}: {sg['description']}
- ASIL: {sg['asil']}
- FSRs: {len(sg_fsrs)}
- Safe State: {sg.get('safe_state', 'Not specified')}
- FTTI: {sg.get('ftti', 'Not specified')}
"""
    
    prompt += f"""

**Total FSRs:** {len(fsrs)}
**Allocated FSRs:** {len([f for f in fsrs if f.get('allocated_to')])}
"""
    
    try:
        verification_report = cat.llm(prompt).strip()
        
        # Store verification report
        cat.working_memory["fsc_verification_report"] = verification_report
        cat.working_memory["fsc_stage"] = "fsc_verified"
        
        # Parse verification results
        is_compliant = "PASS" in verification_report and "FAIL" not in verification_report[:500]
        
        summary = f"""✅ **FSC Verification Complete**
*ISO 26262-3:2018, Clause 7.4.4 and ISO 26262-8:2018, Clause 9*

**System:** {system_name}
**Verification Date:** {datetime.now().strftime("%Y-%m-%d")}

**Verification Scope:**
✅ a) Consistency and compliance with safety goals
✅ b) Ability to mitigate or avoid hazards

**Verification Status:** {'✅ COMPLIANT' if is_compliant else '⚠️ REQUIRES ATTENTION'}

---

**Detailed Verification Report:**

{verification_report}

---

**ISO 26262-3:2018 Compliance:**
✅ 7.4.4.1: FSC verified per ISO 26262-8:2018, Clause 9
✅ Evidence for consistency and compliance
✅ Evidence for hazard mitigation capability

**Next Steps:**

1. **Address any issues identified** (if applicable)
   
2. **Generate FSC Work Products (7.5):**
   `generate FSC document`
   - Will include this verification report per 7.5.2
"""
        
        return summary
        
    except Exception as e:
        log.error(f"Error verifying FSC: {e}")
        import traceback
        log.error(traceback.format_exc())
        return f"❌ Error verifying FSC: {str(e)}"


def parse_validation_criteria(llm_response, safety_goals, fsrs):
    """
    Parse validation criteria from LLM response.
    """
    
    validation_criteria = []
    current_vc = {}
    
    lines = llm_response.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Detect validation criterion entry
        if line.startswith('**VC-'):
            # Save previous criterion
            if current_vc:
                validation_criteria.append(current_vc)
            
            # Start new criterion
            vc_id = line.split('**')[1].strip()
            current_vc = {
                'id': vc_id,
                'validation_method': '',
                'test_conditions': '',
                'success_criteria': ''
            }
    
    # Save last criterion
    if current_vc:
        validation_criteria.append(current_vc)
    
    log.info(f"✅ Parsed {len(validation_criteria)} validation criteria")
    return validation_criteria