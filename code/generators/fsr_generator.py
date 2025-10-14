# generators/fsr_generator.py
# Business logic for deriving Functional Safety Requirements per ISO 26262-3:2018, Clause 7.4.2

from typing import List, Dict, Optional, Callable
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import SafetyGoal, SafetyStrategy, FunctionalSafetyRequirement
from core.constants import FSR_TYPE_CODES, DEFAULT_OPERATING_MODES


class FSRGenerator:
    """
    Derives Functional Safety Requirements from safety goals and strategies.
    Per ISO 26262-3:2018, Clause 7.4.2
    
    - At least one FSR per safety goal (7.4.2.2)
    - FSRs consider all required aspects (7.4.2.4)
    - FSRs are measurable and verifiable
    """
    
    def __init__(self, llm_function: Callable[[str], str]):
        """
        Initialize FSR generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
        """
        self.llm = llm_function
    
    def generate_fsrs(self, safety_goals: List[SafetyGoal], 
                     strategies: List[SafetyStrategy],
                     system_name: str = "the system") -> List[FunctionalSafetyRequirement]:
        """
        Generate FSRs for all safety goals.
        
        Args:
            safety_goals: List of SafetyGoal objects
            strategies: List of SafetyStrategy objects (optional, improves FSR quality)
            system_name: Name of the system
            
        Returns:
            List of FunctionalSafetyRequirement objects
        """
        # Build prompt for all goals
        prompt = self._build_fsr_prompt(safety_goals, strategies, system_name)
        
        # Get LLM response
        try:
            response = self.llm(prompt)
            
            # Parse FSRs from response
            fsrs = self._parse_fsrs(response, safety_goals)
            
            return fsrs
            
        except Exception as e:
            print(f"Error generating FSRs: {e}")
            return []
    
    def _build_fsr_prompt(self, safety_goals: List[SafetyGoal],
                         strategies: List[SafetyStrategy],
                         system_name: str) -> str:
        """
        Build LLM prompt for FSR derivation.
        
        Args:
            safety_goals: List of SafetyGoal objects
            strategies: List of SafetyStrategy objects
            system_name: Name of the system
            
        Returns:
            Prompt string
        """
        prompt = f"""You are deriving Functional Safety Requirements (FSRs) per ISO 26262-3:2018, Clause 7.4.2.

**System:** {system_name}
**Number of Safety Goals:** {len(safety_goals)}

**Requirements per ISO 26262-3:2018:**
- 7.4.2.2: At least ONE FSR per safety goal (aim for 5-10 FSRs per goal)
- 7.4.2.4: Each FSR shall consider:
  a) Operating modes
  b) Fault tolerant time interval (FTTI)
  c) Safe states
  d) Emergency operation time interval (if applicable)
  e) Functional redundancies (if applicable)

**FSR Categories (use these ID formats):**
- **FSR-[SG-ID]-AVD-n**: Fault Avoidance (7.4.2.3.a)
- **FSR-[SG-ID]-DET-n**: Fault Detection (7.4.2.3.b)
- **FSR-[SG-ID]-CTL-n**: Fault Control (7.4.2.3.b)
- **FSR-[SG-ID]-SST-n**: Safe State Transition (7.4.2.3.c)
- **FSR-[SG-ID]-TOL-n**: Fault Tolerance (7.4.2.3.d)
- **FSR-[SG-ID]-WRN-n**: Warning/Indication (7.4.2.3.f,g)
- **FSR-[SG-ID]-TIM-n**: Timing (7.4.2.3.h)
- **FSR-[SG-ID]-ARB-n**: Arbitration (7.4.2.3.i)

**CRITICAL INSTRUCTIONS:**
- Output ONLY a single markdown table with ALL FSRs
- Do NOT add section headers or explanations
- Start directly with the table header row
- Use exact FSR ID format: FSR-SG-XXX-CATEGORY-N

**Table Columns:**
| FSR ID | FSR Description | FSR Allocation | FSR ASIL | Linked Safety Goal | Validation and Verification Criteria | Time Constraints FTTI |

**Example Row:**
| FSR-SG-001-DET-1 | Detect voltage deviation >5% within 50ms | Voltage Monitor Hardware | C | SG-001 | HIL test with fault injection under all operating modes | 50ms |

**FSR Quality Requirements:**
- Measurable (include thresholds, timing)
- Verifiable (testable)
- Specific (not vague)
- Complete (covers all aspects)
- Traceable to safety goal

**Safety Goals to Derive FSRs From:**

"""
        
        for goal in safety_goals:
            if not goal.is_safety_relevant():
                continue
            
            prompt += f"\n### {goal.id}\n"
            prompt += f"**Safety Goal:** {goal.description}\n"
            prompt += f"**ASIL:** {goal.asil}\n"
            prompt += f"**Safe State:** {goal.safe_state if goal.safe_state else 'To be specified'}\n"
            prompt += f"**FTTI:** {goal.ftti if goal.ftti else 'To be determined'}\n"
            
            # Add strategy if available
            strategy = next((s for s in strategies if s.safety_goal_id == goal.id), None)
            if strategy and strategy.strategies:
                prompt += f"\n**Key Strategies:**\n"
                for key in ['fault_detection', 'fault_control', 'safe_state_transition']:
                    if key in strategy.strategies:
                        prompt += f"- {strategy.strategies[key][:100]}...\n"
            
            prompt += "\n"
        
        prompt += """

**Now generate FSRs in TABLE FORMAT ONLY. Start with the header row:**
"""
        
        return prompt
    
    def _parse_fsrs(self, llm_response: str, 
                   safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """
        Parse FSRs from LLM response.
        
        Args:
            llm_response: LLM output containing FSRs
            safety_goals: List of safety goals for reference
            
        Returns:
            List of FunctionalSafetyRequirement objects
        """
        # Try table format first
        fsrs = self._parse_fsrs_from_table(llm_response, safety_goals)
        
        if fsrs:
            return fsrs
        
        # Fallback to structured text format
        fsrs = self._parse_fsrs_from_text(llm_response, safety_goals)
        
        return fsrs
    
    def _parse_fsrs_from_table(self, response: str, 
                               safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """
        Parse FSRs from markdown table format.
        
        Expected format:
        | FSR ID | Description | Allocation | ASIL | Linked SG | Verification | FTTI |
        """
        fsrs = []
        lines = response.strip().split('\n')
        
        # Find table header
        header_idx = None
        for i, line in enumerate(lines):
            if '| FSR ID |' in line or '|FSR ID|' in line or 'FSR ID' in line:
                header_idx = i
                break
        
        if header_idx is None:
            return []
        
        # Parse table rows (skip header and separator)
        for i in range(header_idx + 2, len(lines)):
            line = lines[i].strip()
            
            if not line or not line.startswith('|'):
                continue
            
            # Parse cells
            cells = [cell.strip() for cell in line.split('|')]
            cells = [c for c in cells if c]  # Remove empty
            
            if len(cells) < 5:
                continue
            
            try:
                fsr_id = cells[0]
                description = cells[1]
                allocation = cells[2] if len(cells) > 2 else 'TBD'
                asil = cells[3] if len(cells) > 3 else 'Unknown'
                linked_sg = cells[4] if len(cells) > 4 else 'Unknown'
                verification = cells[5] if len(cells) > 5 else 'TBD'
                timing = cells[6] if len(cells) > 6 else 'TBD'
                
                # Validate FSR ID format
                if not re.search(r'FSR-\w+-\w+-\d+', fsr_id):
                    continue
                
                # Extract safety goal ID
                sg_match = re.search(r'SG-\d+', fsr_id)
                if sg_match:
                    sg_id = sg_match.group(0)
                else:
                    sg_id = linked_sg
                
                # Find parent safety goal
                parent_sg = next((g for g in safety_goals if g.id == sg_id), None)
                if not parent_sg:
                    continue
                
                # Determine FSR type
                fsr_type = self._determine_fsr_type(fsr_id)
                
                # Create FSR object
                fsr = FunctionalSafetyRequirement(
                    id=fsr_id,
                    safety_goal_id=parent_sg.id,
                    safety_goal=parent_sg.description,
                    description=description,
                    asil=asil.strip().upper(),
                    type=fsr_type,
                    operating_modes=DEFAULT_OPERATING_MODES,
                    timing=timing if timing != 'N/A' else parent_sg.ftti,
                    safe_state=parent_sg.safe_state,
                    allocated_to=allocation,
                    verification_criteria=verification,
                    emergency_operation='',
                    functional_redundancy=''
                )
                
                fsrs.append(fsr)
                
            except Exception as e:
                print(f"Error parsing FSR from line {i}: {e}")
                continue
        
        return fsrs
    
    def _parse_fsrs_from_text(self, response: str,
                             safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """
        Parse FSRs from structured text format.
        
        Fallback parser for non-table format.
        """
        fsrs = []
        lines = response.split('\n')
        
        current_fsr = {}
        current_sg_id = None
        
        for line in lines:
            line = line.strip()
            
            # Detect safety goal section
            if line.startswith('## FSRs for') or line.startswith('### '):
                sg_match = re.search(r'SG-\d+', line)
                if sg_match:
                    current_sg_id = sg_match.group(0)
            
            # Detect FSR ID
            if line.startswith('**FSR-') and line.endswith('**'):
                # Save previous FSR
                if current_fsr and 'id' in current_fsr:
                    fsr = self._finalize_fsr(current_fsr, safety_goals)
                    if fsr:
                        fsrs.append(fsr)
                
                # Start new FSR
                fsr_id = line.replace('**', '').strip()
                current_fsr = {
                    'id': fsr_id,
                    'safety_goal_id': current_sg_id or self._extract_sg_from_fsr_id(fsr_id)
                }
            
            # Parse FSR fields
            elif current_fsr:
                if line.startswith('- **Description:**') or line.startswith('**Description:**'):
                    current_fsr['description'] = re.sub(r'\*\*Description:\*\*\s*', '', line).replace('- ', '')
                elif line.startswith('- **ASIL:**') or line.startswith('**ASIL:**'):
                    current_fsr['asil'] = re.sub(r'\*\*ASIL:\*\*\s*', '', line).replace('- ', '')
                elif 'Allocation' in line and (':**' in line):
                    current_fsr['allocated_to'] = line.split(':**')[1].strip() if ':**' in line else 'TBD'
                elif 'Verification' in line and (':**' in line):
                    current_fsr['verification_criteria'] = line.split(':**')[1].strip() if ':**' in line else 'TBD'
        
        # Save last FSR
        if current_fsr and 'id' in current_fsr:
            fsr = self._finalize_fsr(current_fsr, safety_goals)
            if fsr:
                fsrs.append(fsr)
        
        return fsrs
    
    def _finalize_fsr(self, fsr_data: Dict, 
                     safety_goals: List[SafetyGoal]) -> Optional[FunctionalSafetyRequirement]:
        """
        Convert parsed FSR dictionary to FunctionalSafetyRequirement object.
        
        Args:
            fsr_data: Dictionary with parsed FSR data
            safety_goals: List of safety goals
            
        Returns:
            FunctionalSafetyRequirement object or None
        """
        sg_id = fsr_data.get('safety_goal_id')
        parent_sg = next((sg for sg in safety_goals if sg.id == sg_id), None)
        
        if not parent_sg:
            return None
        
        fsr_type = self._determine_fsr_type(fsr_data.get('id', ''))
        
        return FunctionalSafetyRequirement(
            id=fsr_data.get('id', 'Unknown'),
            safety_goal_id=sg_id,
            safety_goal=parent_sg.description,
            description=fsr_data.get('description', 'Not specified'),
            asil=fsr_data.get('asil', parent_sg.asil),
            type=fsr_type,
            operating_modes=DEFAULT_OPERATING_MODES,
            timing=parent_sg.ftti,
            safe_state=parent_sg.safe_state,
            allocated_to=fsr_data.get('allocated_to', 'TBD'),
            verification_criteria=fsr_data.get('verification_criteria', 'TBD'),
            emergency_operation='',
            functional_redundancy=''
        )
    
    def _determine_fsr_type(self, fsr_id: str) -> str:
        """
        Determine FSR type from ID.
        
        Args:
            fsr_id: FSR identifier
            
        Returns:
            FSR type name
        """
        type_mapping = {
            'AVD': 'Fault Avoidance',
            'DET': 'Fault Detection',
            'CTL': 'Fault Control',
            'SST': 'Safe State Transition',
            'TOL': 'Fault Tolerance',
            'WRN': 'Warning/Indication',
            'TIM': 'Timing',
            'ARB': 'Arbitration'
        }
        
        for code, name in type_mapping.items():
            if f'-{code}-' in fsr_id:
                return name
        
        return 'General'
    
    def _extract_sg_from_fsr_id(self, fsr_id: str) -> str:
        """
        Extract safety goal ID from FSR ID.
        
        Args:
            fsr_id: FSR identifier
            
        Returns:
            Safety goal ID or 'Unknown'
        """
        match = re.search(r'SG-\d+', fsr_id)
        return match.group(0) if match else 'Unknown'


class FSRFormatter:
    """Helper class for formatting FSR output"""
    
    @staticmethod
    def format_fsr_summary(fsrs: List[FunctionalSafetyRequirement],
                          safety_goals: List[SafetyGoal],
                          system_name: str) -> str:
        """
        Format FSRs into a readable summary.
        
        Args:
            fsrs: List of FSR objects
            safety_goals: List of SafetyGoal objects
            system_name: System name
            
        Returns:
            Formatted summary string
        """
        if not fsrs:
            return "No FSRs generated."
        
        summary = f"# Functional Safety Requirements\n\n"
        summary += f"**System:** {system_name}\n"
        summary += f"**Total FSRs:** {len(fsrs)}\n\n"
        
        # FSR statistics
        asil_counts = {}
        type_counts = {}
        
        for fsr in fsrs:
            asil_counts[fsr.asil] = asil_counts.get(fsr.asil, 0) + 1
            type_counts[fsr.type] = type_counts.get(fsr.type, 0) + 1
        
        summary += "**ASIL Distribution:**\n"
        for asil in ['D', 'C', 'B', 'A']:
            if asil in asil_counts:
                summary += f"- ASIL {asil}: {asil_counts[asil]} FSRs\n"
        
        summary += "\n**FSR Types:**\n"
        for fsr_type, count in sorted(type_counts.items()):
            summary += f"- {fsr_type}: {count} FSRs\n"
        
        summary += "\n---\n\n"
        
        # Group FSRs by safety goal
        for goal in safety_goals:
            goal_fsrs = [f for f in fsrs if f.safety_goal_id == goal.id]
            
            if not goal_fsrs:
                continue
            
            summary += f"## {goal.id}: {goal.description}\n\n"
            summary += f"**ASIL:** {goal.asil}\n"
            summary += f"**FSRs:** {len(goal_fsrs)}\n\n"
            
            for fsr in goal_fsrs:
                summary += f"### {fsr.id}\n"
                summary += f"**Type:** {fsr.type}\n"
                summary += f"**Description:** {fsr.description}\n"
                summary += f"**ASIL:** {fsr.asil}\n"
                summary += f"**Allocated To:** {fsr.allocated_to}\n"
                summary += f"**Verification:** {fsr.verification_criteria}\n"
                summary += f"**Timing:** {fsr.timing}\n\n"
            
            summary += "---\n\n"
        
        return summary
    
    @staticmethod
    def format_fsr_table(fsrs: List[FunctionalSafetyRequirement]) -> str:
        """
        Format FSRs as markdown table.
        
        Args:
            fsrs: List of FSR objects
            
        Returns:
            Markdown table string
        """
        table = "| FSR ID | Description | Type | ASIL | Allocated To | Verification |\n"
        table += "|--------|-------------|------|------|--------------|-------------|\n"
        
        for fsr in fsrs:
            desc = fsr.description[:60] + "..." if len(fsr.description) > 60 else fsr.description
            alloc = fsr.allocated_to[:30] + "..." if len(fsr.allocated_to) > 30 else fsr.allocated_to
            verif = fsr.verification_criteria[:40] + "..." if len(fsr.verification_criteria) > 40 else fsr.verification_criteria
            
            table += f"| {fsr.id} | {desc} | {fsr.type} | {fsr.asil} | {alloc} | {verif} |\n"
        
        return table