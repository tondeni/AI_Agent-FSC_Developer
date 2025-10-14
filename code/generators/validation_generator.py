# generators/validation_generator.py
# Business logic for generating safety validation criteria per ISO 26262-3:2018, Clause 7.4.3

from typing import List, Dict, Optional, Callable
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import (
    SafetyGoal, 
    FunctionalSafetyRequirement, 
    ValidationCriterion
)


class ValidationGenerator:
    """
    Generates safety validation criteria for FSRs and safety goals.
    Per ISO 26262-3:2018, Clause 7.4.3
    
    - Specifies acceptance criteria for safety validation
    - Based on functional safety requirements and safety goals
    - Supports ISO 26262-4:2018, Clause 8 (Safety Validation)
    """
    
    def __init__(self, llm_function: Callable[[str], str]):
        """
        Initialize validation generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
        """
        self.llm = llm_function
    
    def generate_validation_criteria(self, 
                                    safety_goals: List[SafetyGoal],
                                    fsrs: List[FunctionalSafetyRequirement],
                                    system_name: str = "the system") -> List[ValidationCriterion]:
        """
        Generate validation criteria for all FSRs and safety goals.
        
        Args:
            safety_goals: List of SafetyGoal objects
            fsrs: List of FSR objects
            system_name: Name of the system
            
        Returns:
            List of ValidationCriterion objects
        """
        # Build prompt
        prompt = self._build_validation_prompt(safety_goals, fsrs, system_name)
        
        # Get LLM response
        try:
            response = self.llm(prompt)
            
            # Parse validation criteria
            criteria = self._parse_validation_criteria(response, safety_goals, fsrs)
            
            return criteria
            
        except Exception as e:
            print(f"Error generating validation criteria: {e}")
            return []
    
    def _build_validation_prompt(self, 
                                 safety_goals: List[SafetyGoal],
                                 fsrs: List[FunctionalSafetyRequirement],
                                 system_name: str) -> str:
        """
        Build LLM prompt for validation criteria generation.
        
        Args:
            safety_goals: List of SafetyGoal objects
            fsrs: List of FSR objects
            system_name: System name
            
        Returns:
            Prompt string
        """
        prompt = f"""You are specifying Safety Validation Criteria per ISO 26262-3:2018, Clause 7.4.3.

**System:** {system_name}
**Safety Goals:** {len(safety_goals)}
**FSRs:** {len(fsrs)}

**ISO 26262-3:2018, 7.4.3.1 Requirement:**

The acceptance criteria for safety validation of the item shall be specified based on:
- The functional safety requirements
- The safety goals

**NOTE 1:** For further requirements on detailing the criteria and list of characteristics 
to be validated, see ISO 26262-4:2018, Clause 8.

**NOTE 2:** Safety validation of safety goals is addressed on upper right of V-model but 
is included in activities during development and not only performed at the end.

**Your Task:**

For each safety goal and its associated FSRs, specify measurable acceptance criteria that 
will be used during safety validation (ISO 26262-4:2018, Clause 8).

**Validation Criteria Structure:**

For each Safety Goal:

1. **Goal-Level Acceptance Criteria**
   - How to validate the safety goal is achieved
   - Overall system behavior validation
   - Integration with vehicle-level validation

2. **FSR-Level Acceptance Criteria**
   - For each FSR, define specific acceptance criteria
   - Measurable pass/fail criteria
   - Test methods and conditions
   - Success criteria with quantitative thresholds

3. **Characteristics to be Validated** (per ISO 26262-4:2018, Clause 8)
   - Functional behavior (nominal and degraded modes)
   - Fault detection capability and coverage
   - Safe state transitions (timing and completeness)
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

**Validation Method:** [Test/Analysis/Inspection/Review]
- Test Type: [Unit/Integration/System/Vehicle-level]
- Test Environment: [Bench/HIL/SIL/Vehicle]

**Test Conditions:**
- Normal operating conditions: [specific conditions]
- Environmental conditions: [temperature, voltage, etc.]
- Fault injection scenarios: [specific faults to inject]
- Operating modes: [all applicable modes]

**Success Criteria:**
- Quantifiable pass criteria: [specific thresholds]
- Acceptable ranges: [min/max values]
- Performance requirements: [timing, accuracy]
- Coverage requirements: [% coverage for diagnostics]

**Evidence Required:**
- Test reports with results
- Analysis documentation
- Validation documentation per ISO 26262-4

---

### FSR-Level Acceptance Criteria

**VC-FSR-[FSR-ID]**

**FSR:** [FSR description]
**Type:** [Detection/Control/Transition/etc.]
**ASIL:** [X]

**Criterion:** [Specific, measurable acceptance criterion]

**Validation Method:**
- Primary Method: [HIL Test/SIL/Vehicle Test/Analysis]
- Supporting Methods: [Additional methods if needed]

**Test Conditions:**
- Normal operation scenarios
- Degraded operation scenarios
- Fault conditions: [specific faults to inject]
- Operating modes: [all applicable modes]
- Environmental conditions: [temperature range, voltage range, etc.]

**Success Criteria:**
- Quantitative criteria: [with specific thresholds]
- Timing requirements: [detection time ≤ X ms, reaction time ≤ Y ms]
- Accuracy requirements: [error ≤ X%]
- Coverage requirements: [diagnostic coverage ≥ X%]
- Performance requirements: [specific KPIs]

**Pass/Fail Determination:**
- Pass: [explicit conditions for pass]
- Fail: [explicit conditions for fail]

**Traceability:**
- Validates FSR: [FSR-ID]
- Supports Safety Goal: [SG-ID]
- ASIL: [Inherited ASIL]

---

**Validation Characteristics per ISO 26262-4:2018, Clause 8:**

For each safety goal, address these characteristics:

1. **Functional Behavior:**
   - Nominal behavior validation (expected functionality)
   - Degraded functionality validation (reduced performance)
   - Limp-home mode validation (safe minimal functionality)

2. **Fault Detection:**
   - Detection coverage validation (≥ target coverage per ASIL)
   - Detection time validation (≤ FTTI requirement)
   - False positive rate validation (acceptably low)

3. **Safe State Transitions:**
   - Transition timing validation (≤ FTTI)
   - Safe state maintenance validation (stays in safe state)
   - Recovery validation (if applicable)

4. **Timing Performance:**
   - FTTI compliance validation
   - Fault handling time interval validation
   - Response time validation for all scenarios

5. **Warnings/Indications:**
   - Warning presentation validation (clear and unambiguous)
   - Driver perception validation (driver understands warning)
   - Controllability improvement validation (warning helps driver)

6. **Fault Tolerance:**
   - Redundancy validation (backup functions work)
   - Degradation behavior validation (graceful degradation)
   - Fail-operational capability validation (if applicable)

---

**Safety Goals and FSRs to Generate Criteria For:**

"""
        
        for sg in safety_goals:
            prompt += f"""
### {sg.id}
**Safety Goal:** {sg.description}
**ASIL:** {sg.asil}
**Safe State:** {sg.safe_state if sg.safe_state else 'To be specified'}
**FTTI:** {sg.ftti if sg.ftti else 'TBD'}

**Associated FSRs:**
"""
            
            sg_fsrs = [f for f in fsrs if f.safety_goal_id == sg.id]
            for fsr in sg_fsrs[:5]:  # Show first 5
                prompt += f"   - {fsr.id}: {fsr.type} - {fsr.description[:60]}...\n"
            
            if len(sg_fsrs) > 5:
                prompt += f"   - ... and {len(sg_fsrs) - 5} more FSRs\n"
            
            prompt += "\n"
        
        prompt += """
**Requirements:**
- Criteria must be measurable and testable
- Include both qualitative and quantitative criteria
- Specify test conditions and success criteria clearly
- Consider all operating modes and fault conditions
- Align with ASIL requirements (higher ASIL = more stringent criteria)
- Support safety validation per ISO 26262-4:2018, Clause 8
- Provide sufficient detail for test engineers to implement

**Now specify comprehensive safety validation criteria for all safety goals and FSRs.**
"""
        
        return prompt
    
    def _parse_validation_criteria(self, 
                                   llm_response: str,
                                   safety_goals: List[SafetyGoal],
                                   fsrs: List[FunctionalSafetyRequirement]) -> List[ValidationCriterion]:
        """
        Parse validation criteria from LLM response.
        
        Args:
            llm_response: LLM output text
            safety_goals: List of SafetyGoal objects
            fsrs: List of FSR objects
            
        Returns:
            List of ValidationCriterion objects
        """
        criteria = []
        lines = llm_response.split('\n')
        
        current_criterion = {}
        current_type = None  # 'goal' or 'fsr'
        
        for line in lines:
            line = line.strip()
            
            # Detect criterion entry
            if line.startswith('**VC-'):
                # Save previous criterion
                if current_criterion:
                    criterion = self._finalize_criterion(current_criterion, safety_goals, fsrs)
                    if criterion:
                        criteria.append(criterion)
                
                # Start new criterion
                vc_id = line.split('**')[1].strip()
                
                # Determine type
                if '-GOAL' in vc_id:
                    current_type = 'goal'
                    sg_id = re.search(r'SG-\d+', vc_id)
                    current_criterion = {
                        'id': vc_id,
                        'type': 'goal',
                        'safety_goal_id': sg_id.group(0) if sg_id else 'Unknown',
                        'fsr_id': None
                    }
                elif '-FSR-' in vc_id or 'FSR-' in vc_id:
                    current_type = 'fsr'
                    fsr_match = re.search(r'FSR-[A-Z]+-\d+-[A-Z]+-\d+', vc_id)
                    if fsr_match:
                        fsr_id = fsr_match.group(0)
                        # Extract SG from FSR
                        sg_match = re.search(r'SG-\d+', fsr_id)
                        current_criterion = {
                            'id': vc_id,
                            'type': 'fsr',
                            'fsr_id': fsr_id,
                            'safety_goal_id': sg_match.group(0) if sg_match else 'Unknown'
                        }
            
            # Parse criterion fields
            elif current_criterion:
                if line.startswith('**Criterion:**'):
                    current_criterion['criterion'] = line.replace('**Criterion:**', '').strip()
                elif line.startswith('**Validation Method:**'):
                    current_criterion['validation_method'] = line.replace('**Validation Method:**', '').strip()
                elif 'Test Conditions:' in line or 'Test conditions:' in line:
                    # Start capturing test conditions
                    current_criterion['test_conditions_flag'] = True
                    current_criterion['test_conditions'] = ''
                elif current_criterion.get('test_conditions_flag') and line.startswith('-'):
                    current_criterion['test_conditions'] += line + '\n'
                elif 'Success Criteria:' in line:
                    current_criterion['test_conditions_flag'] = False
                    current_criterion['success_criteria_flag'] = True
                    current_criterion['success_criteria'] = ''
                elif current_criterion.get('success_criteria_flag') and line.startswith('-'):
                    current_criterion['success_criteria'] += line + '\n'
                elif 'Evidence Required:' in line:
                    current_criterion['success_criteria_flag'] = False
                    current_criterion['evidence_flag'] = True
                    current_criterion['evidence_required'] = ''
                elif current_criterion.get('evidence_flag') and line.startswith('-'):
                    current_criterion['evidence_required'] += line + '\n'
        
        # Save last criterion
        if current_criterion:
            criterion = self._finalize_criterion(current_criterion, safety_goals, fsrs)
            if criterion:
                criteria.append(criterion)
        
        return criteria
    
    def _finalize_criterion(self, 
                           criterion_data: Dict,
                           safety_goals: List[SafetyGoal],
                           fsrs: List[FunctionalSafetyRequirement]) -> Optional[ValidationCriterion]:
        """
        Convert parsed criterion dictionary to ValidationCriterion object.
        
        Args:
            criterion_data: Dictionary with parsed data
            safety_goals: List of safety goals
            fsrs: List of FSRs
            
        Returns:
            ValidationCriterion object or None
        """
        if not criterion_data.get('id'):
            return None
        
        return ValidationCriterion(
            id=criterion_data.get('id', 'Unknown'),
            fsr_id=criterion_data.get('fsr_id', ''),
            safety_goal_id=criterion_data.get('safety_goal_id', ''),
            criterion=criterion_data.get('criterion', 'Not specified'),
            validation_method=criterion_data.get('validation_method', 'To be determined'),
            test_conditions=criterion_data.get('test_conditions', ''),
            success_criteria=criterion_data.get('success_criteria', ''),
            evidence_required=criterion_data.get('evidence_required', '')
        )


class ValidationFormatter:
    """Helper class for formatting validation criteria output"""
    
    @staticmethod
    def format_validation_summary(criteria: List[ValidationCriterion],
                                  safety_goals: List[SafetyGoal],
                                  fsrs: List[FunctionalSafetyRequirement],
                                  system_name: str) -> str:
        """
        Format validation criteria into a readable summary.
        
        Args:
            criteria: List of ValidationCriterion objects
            safety_goals: List of SafetyGoal objects
            fsrs: List of FSR objects
            system_name: System name
            
        Returns:
            Formatted summary string
        """
        if not criteria:
            return "No validation criteria generated."
        
        summary = f"# Safety Validation Criteria\n\n"
        summary += f"**System:** {system_name}\n"
        summary += f"**Total Criteria:** {len(criteria)}\n\n"
        
        # Statistics
        goal_criteria = [c for c in criteria if not c.fsr_id]
        fsr_criteria = [c for c in criteria if c.fsr_id]
        
        summary += f"**Goal-Level Criteria:** {len(goal_criteria)}\n"
        summary += f"**FSR-Level Criteria:** {len(fsr_criteria)}\n\n"
        
        # Validation methods
        methods = {}
        for criterion in criteria:
            method = criterion.validation_method.split('-')[0].strip() if criterion.validation_method else 'Unknown'
            methods[method] = methods.get(method, 0) + 1
        
        summary += "**Validation Methods:**\n"
        for method, count in sorted(methods.items()):
            summary += f"- {method}: {count} criteria\n"
        
        summary += "\n---\n\n"
        
        # Group by safety goal
        for goal in safety_goals:
            goal_criteria_list = [c for c in criteria if c.safety_goal_id == goal.id]
            
            if not goal_criteria_list:
                continue
            
            summary += f"## {goal.id}: {goal.description}\n\n"
            summary += f"**ASIL:** {goal.asil}\n"
            summary += f"**Validation Criteria:** {len(goal_criteria_list)}\n\n"
            
            for criterion in goal_criteria_list:
                summary += f"### {criterion.id}\n"
                summary += f"**Criterion:** {criterion.criterion}\n"
                summary += f"**Method:** {criterion.validation_method}\n"
                
                if criterion.test_conditions:
                    summary += f"**Test Conditions:**\n{criterion.test_conditions}\n"
                
                if criterion.success_criteria:
                    summary += f"**Success Criteria:**\n{criterion.success_criteria}\n"
                
                summary += "\n"
            
            summary += "---\n\n"
        
        return summary
    
    @staticmethod
    def get_validation_statistics(criteria: List[ValidationCriterion]) -> Dict:
        """
        Generate statistics about validation criteria.
        
        Args:
            criteria: List of ValidationCriterion objects
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total': len(criteria),
            'goal_level': len([c for c in criteria if not c.fsr_id]),
            'fsr_level': len([c for c in criteria if c.fsr_id]),
            'by_method': {},
            'by_safety_goal': {}
        }
        
        for criterion in criteria:
            # By method
            method = criterion.validation_method.split('-')[0].strip() if criterion.validation_method else 'Unknown'
            stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
            
            # By safety goal
            sg = criterion.safety_goal_id
            if sg not in stats['by_safety_goal']:
                stats['by_safety_goal'][sg] = 0
            stats['by_safety_goal'][sg] += 1
        
        return stats