# generators/fsr_generator.py
# Business logic for deriving Functional Safety Requirements per ISO 26262-3:2018, Clause 7.4.2

from typing import List, Dict, Optional, Callable
from core.models import SafetyGoal, SafetyStrategy, FunctionalSafetyRequirement
from core.constants import FSR_TYPE_CODES, DEFAULT_OPERATING_MODES
from cat.log import log
from settings import FSCDeveloperSettings
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class FSRGenerator:
    """
    Derives Functional Safety Requirements from safety goals and strategies.
    Per ISO 26262-3:2018, Clause 7.4.2
    """
    
    def __init__(self, llm_function, max_fsr_per_safety_goal: int):
        """
        Initialize FSR generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
            max_fsr_per_safety_goal: Maximum FSRs per safety goal
        """
        self.llm = llm_function
        self.max_fsr_per_safety_goal = max_fsr_per_safety_goal
    
    def generate_fsrs(self, 
                      safety_goals: List[SafetyGoal], 
                      strategies: List[SafetyStrategy], 
                      max_fsr_per_safety_goal: int,
                      system_name: str = "the system") -> List[FunctionalSafetyRequirement]:
        """Generate FSRs for all safety goals."""
        
        prompt = self._build_fsr_prompt(safety_goals, strategies, max_fsr_per_safety_goal, system_name)
        
        try:
            log.info("🤖 Calling LLM for FSR generation")
            response = self.llm(prompt)
            
            log.info(f"📥 Received LLM response ({len(response)} chars)")
            log.info("=" * 80)
            log.info("LLM RESPONSE PREVIEW:")
            log.info(response[:1000] if len(response) > 1000 else response)
            log.info("=" * 80)
            
            fsrs = self._parse_fsrs(response, safety_goals)
            
            if fsrs:
                log.info(f"✅ Successfully parsed {len(fsrs)} FSRs")
            else:
                log.warning("⚠️ No FSRs parsed from response")
            
            return fsrs
            
        except Exception as e:
            log.error(f"❌ Error generating FSRs: {e}")
            import traceback
            log.error(traceback.format_exc())
            return []
    
    def _build_fsr_prompt(self, 
                         safety_goals: List[SafetyGoal],
                         strategies: List[SafetyStrategy],
                         max_fsr_per_safety_goal: int,
                         system_name: str) -> str:
        """Build LLM prompt with VERY clear format instructions."""
        
        prompt = f"""You are an ISO 26262 Functional Safety expert deriving Functional Safety Requirements (FSRs).

**System:** {system_name}
**Task:** Derive {max_fsr_per_safety_goal} FSRs for each safety goal below.

**CRITICAL: You MUST use this EXACT format for each FSR:**

```
FSR-ID: FSR-SG-001-DET-1
Description: The system shall detect battery voltage deviation greater than 5% from nominal value
Category: Detection
ASIL: C
Safety Goal: SG-001
Allocation: Battery Voltage Sensor
Verification: Test with simulated voltage variations
FTTI: 100ms
---
```

**Important Rules:**
1. Start each FSR with "FSR-ID:" (exactly this format)
2. End each FSR with "---" (three dashes)
3. Include ALL fields for each FSR
4. Use these categories: Detection, Control, Warning, Avoidance, Safe State, Tolerance, Timing, Arbitration
5. FSR ID format: FSR-SG-ID-TYPE-NUMBER
   - Example: FSR-SG-001-DET-1, FSR-SG-001-CTL-1, FSR-SG-002-DET-1

**Safety Goals:**

"""
        
        # Add safety goals with context
        for goal in safety_goals:
            if not goal.is_safety_relevant():
                continue
            
            prompt += f"\n**{goal.id}**: {goal.description}\n"
            prompt += f"- ASIL: {goal.asil}\n"
            prompt += f"- Safe State: {goal.safe_state if goal.safe_state else 'To be specified'}\n"
            prompt += f"- FTTI: {goal.ftti if goal.ftti else 'To be determined'}\n"
            
            # Add strategies if available
            # Commented out since there is a issue with strategy_type (not defined)
            # goal_strategies = [s for s in strategies if s.safety_goal_id == goal.id]
            # if goal_strategies:
            #     prompt += "- Key Strategies:\n"
            #     for strategy in goal_strategies[:2]:
            #         prompt += f"  * {strategy.strategy_type}: {strategy.description[:80]}...\n"
            
            prompt += "\n"
        
        prompt += f"""
**Generate {max_fsr_per_safety_goal} FSRs for EACH safety goal above.**

Remember:
- Use the EXACT format shown (FSR-ID:, Description:, etc.)
- End each FSR with "---"
- Make FSRs specific and measurable
- Use appropriate categories (Detection, Control, Warning, etc.)

**Start generating FSRs now:**
"""
        
        return prompt
    
    def _parse_fsrs(self, llm_response: str, 
                   safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """Parse FSRs with multiple fallback strategies."""
        
        log.info("Starting FSR parsing")
        
        # Strategy 1: Structured text format (primary)
        fsrs = self._parse_fsrs_from_structured_text(llm_response, safety_goals)
        if fsrs:
            log.info(f"✅ Parsed {len(fsrs)} FSRs from structured text")
            return fsrs
        
        # Strategy 2: Markdown table format (legacy)
        log.info("Trying table format parser")
        fsrs = self._parse_fsrs_from_table(llm_response, safety_goals)
        if fsrs:
            log.info(f"✅ Parsed {len(fsrs)} FSRs from table format")
            return fsrs
        
        # Strategy 3: Regex extraction (aggressive)
        log.info("Trying regex extraction parser")
        fsrs = self._parse_fsrs_with_regex(llm_response, safety_goals)
        if fsrs:
            log.info(f"✅ Parsed {len(fsrs)} FSRs with regex")
            return fsrs
        
        log.error("❌ All parsing strategies failed")
        return []
    
    def _parse_fsrs_from_structured_text(self, response: str,
                                        safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """Parse FSRs from structured text format."""
        
        fsrs = []
        lines = response.strip().split('\n')
        current_fsr = {}
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and code block markers
            if not line or line in ['```', '---']:
                if line == '---' and current_fsr and 'fsr_id' in current_fsr:
                    # FSR block ended
                    fsr = self._create_fsr_from_dict(current_fsr, safety_goals)
                    if fsr:
                        fsrs.append(fsr)
                        log.info(f"Parsed FSR: {fsr.id}")
                    current_fsr = {}
                continue
            
            # Parse "Field: Value" format
            if ':' in line and not line.startswith('#'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    field = parts[0].strip().lower().replace('-', '_').replace(' ', '_')
                    value = parts[1].strip()
                    
                    # Map field names
                    if 'fsr' in field and 'id' in field:
                        current_fsr['fsr_id'] = value
                    elif 'description' in field:
                        current_fsr['description'] = value
                    elif 'category' in field:
                        current_fsr['category'] = value
                    elif 'asil' in field:
                        current_fsr['asil'] = value.upper()
                    elif 'safety' in field and 'goal' in field:
                        current_fsr['safety_goal_id'] = value
                    elif 'allocation' in field or 'allocated' in field:
                        current_fsr['allocated_to'] = value
                    elif 'verification' in field:
                        current_fsr['verification'] = value
                    elif 'ftti' in field or 'timing' in field:
                        current_fsr['timing'] = value
        
        # Save last FSR if exists
        if current_fsr and 'fsr_id' in current_fsr:
            fsr = self._create_fsr_from_dict(current_fsr, safety_goals)
            if fsr:
                fsrs.append(fsr)
                log.info(f"Parsed FSR: {fsr.id}")
        
        return fsrs
    
    def _parse_fsrs_with_regex(self, response: str,
                               safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """Aggressive regex-based extraction as last resort."""
        
        fsrs = []
        
        # Find all FSR IDs in the text
        fsr_id_pattern = r'FSR-SG-\d+-[A-Z]{3}-\d+'
        fsr_ids = re.findall(fsr_id_pattern, response)
        
        log.info(f"Found {len(fsr_ids)} FSR IDs with regex: {fsr_ids}")
        
        for fsr_id in fsr_ids:
            try:
                # Extract safety goal ID
                sg_match = re.search(r'SG-(\d+)', fsr_id)
                if not sg_match:
                    continue
                
                sg_number = sg_match.group(1)
                parent_sg = None
                
                # Find parent safety goal
                for sg_id_variant in [f"SG-{sg_number}", f"SG-{int(sg_number)}"]:
                    parent_sg = next((g for g in safety_goals if g.id == sg_id_variant), None)
                    if parent_sg:
                        break
                
                if not parent_sg:
                    log.warning(f"No parent safety goal for {fsr_id}")
                    continue
                
                # Try to find description near the FSR ID
                # Look for text between this FSR ID and the next one
                fsr_index = response.find(fsr_id)
                next_fsr_index = len(response)
                
                for other_id in fsr_ids:
                    if other_id != fsr_id:
                        other_index = response.find(other_id, fsr_index + 1)
                        if other_index > fsr_index and other_index < next_fsr_index:
                            next_fsr_index = other_index
                
                fsr_section = response[fsr_index:next_fsr_index]
                
                # Extract description (first meaningful line after FSR ID)
                lines = fsr_section.split('\n')
                description = "Functional safety requirement"
                
                for line in lines[1:10]:  # Check next few lines
                    line = line.strip()
                    if line and len(line) > 20 and not line.startswith('FSR-') and ':' not in line[:20]:
                        description = line
                        break
                    elif 'Description:' in line:
                        description = line.split('Description:', 1)[1].strip()
                        break
                
                # Determine FSR type from ID
                fsr_type = self._determine_fsr_type(fsr_id)
                
                # Create FSR
                fsr = FunctionalSafetyRequirement(
                    id=fsr_id,
                    safety_goal_id=parent_sg.id,
                    safety_goal=parent_sg.description,
                    description=description,
                    asil=parent_sg.asil,
                    type=fsr_type,
                    operating_modes=DEFAULT_OPERATING_MODES,
                    timing=parent_sg.ftti,
                    safe_state=parent_sg.safe_state,
                    allocated_to='TBD',
                    verification_criteria='Requirements-based test',
                    emergency_operation='',
                    functional_redundancy=''
                )
                
                fsrs.append(fsr)
                log.info(f"Regex extracted FSR: {fsr_id}")
                
            except Exception as e:
                log.error(f"Error creating FSR from regex for {fsr_id}: {e}")
                continue
        
        return fsrs
    
    def _parse_fsrs_from_table(self, response: str, 
                               safety_goals: List[SafetyGoal]) -> List[FunctionalSafetyRequirement]:
        """Parse FSRs from markdown table format."""
        
        fsrs = []
        lines = response.strip().split('\n')
        
        # Find table header
        header_idx = None
        for i, line in enumerate(lines):
            normalized = line.lower().replace(' ', '')
            if 'fsrid' in normalized or 'fsr-id' in normalized:
                header_idx = i
                break
        
        if header_idx is None:
            return []
        
        # Parse table rows (skip header and separator)
        for i in range(header_idx + 2, len(lines)):
            line = lines[i].strip()
            
            if not line or not '|' in line:
                continue
            
            cells = [cell.strip() for cell in line.split('|')]
            cells = [c for c in cells if c]
            
            if len(cells) < 4:
                continue
            
            try:
                fsr_id = cells[0]
                
                # Validate FSR ID format
                if not re.search(r'FSR-SG-\d+-[A-Z]{3}-\d+', fsr_id):
                    continue
                
                description = cells[1] if len(cells) > 1 else "Not specified"
                allocation = cells[2] if len(cells) > 2 else "TBD"
                asil = cells[3] if len(cells) > 3 else "QM"
                
                # Extract parent safety goal
                sg_match = re.search(r'SG-(\d+)', fsr_id)
                if not sg_match:
                    continue
                
                sg_number = sg_match.group(1)
                parent_sg = None
                
                for sg_id_variant in [f"SG-{sg_number}", f"SG-{int(sg_number)}"]:
                    parent_sg = next((g for g in safety_goals if g.id == sg_id_variant), None)
                    if parent_sg:
                        break
                
                if not parent_sg:
                    continue
                
                fsr_type = self._determine_fsr_type(fsr_id)
                
                fsr = FunctionalSafetyRequirement(
                    id=fsr_id,
                    safety_goal_id=parent_sg.id,
                    safety_goal=parent_sg.description,
                    description=description,
                    asil=asil.strip().upper(),
                    type=fsr_type,
                    operating_modes=DEFAULT_OPERATING_MODES,
                    timing=parent_sg.ftti,
                    safe_state=parent_sg.safe_state,
                    allocated_to=allocation,
                    verification_criteria='Requirements-based test',
                    emergency_operation='',
                    functional_redundancy=''
                )
                
                fsrs.append(fsr)
                log.info(f"Table parsed FSR: {fsr_id}")
                
            except Exception as e:
                log.error(f"Error parsing table row {i}: {e}")
                continue
        
        return fsrs
    
    def _create_fsr_from_dict(self, fsr_data: Dict, 
                             safety_goals: List[SafetyGoal]) -> Optional[FunctionalSafetyRequirement]:
        """Create FunctionalSafetyRequirement from parsed dictionary."""
        
        fsr_id = fsr_data.get('fsr_id', '')
        
        if not fsr_id:
            return None
        
        # Extract safety goal ID
        sg_id = fsr_data.get('safety_goal_id')
        
        if not sg_id or not sg_id.startswith('SG-'):
            # Try to extract from FSR ID
            sg_match = re.search(r'SG-(\d+)', fsr_id)
            if sg_match:
                sg_number = sg_match.group(1)
                for sg_id_variant in [f"SG-{sg_number}", f"SG-{int(sg_number)}"]:
                    parent_sg = next((g for g in safety_goals if g.id == sg_id_variant), None)
                    if parent_sg:
                        sg_id = parent_sg.id
                        break
        
        # Find parent safety goal
        parent_sg = next((g for g in safety_goals if g.id == sg_id), None)
        
        if not parent_sg:
            log.warning(f"No parent safety goal found for FSR {fsr_id}")
            return None
        
        # Determine FSR type
        fsr_type = self._map_category_to_type(fsr_data.get('category', ''))
        if not fsr_type:
            fsr_type = self._determine_fsr_type(fsr_id)
        
        return FunctionalSafetyRequirement(
            id=fsr_id,
            safety_goal_id=parent_sg.id,
            safety_goal=parent_sg.description,
            description=fsr_data.get('description', 'Not specified'),
            asil=fsr_data.get('asil', parent_sg.asil),
            type=fsr_type,
            operating_modes=DEFAULT_OPERATING_MODES,
            timing=fsr_data.get('timing', parent_sg.ftti),
            safe_state=parent_sg.safe_state,
            allocated_to=fsr_data.get('allocated_to', 'TBD'),
            verification_criteria=fsr_data.get('verification', 'Requirements-based test'),
            emergency_operation='',
            functional_redundancy=''
        )
    
    def _map_category_to_type(self, category: str) -> str:
        """Map category name to FSR type."""
        
        category_lower = category.lower()
        
        mapping = {
            'detection': 'Fault Detection',
            'detect': 'Fault Detection',
            'control': 'Fault Control',
            'warning': 'Warning/Indication',
            'warn': 'Warning/Indication',
            'indication': 'Warning/Indication',
            'avoidance': 'Fault Avoidance',
            'avoid': 'Fault Avoidance',
            'safe state': 'Safe State Transition',
            'transition': 'Safe State Transition',
            'tolerance': 'Fault Tolerance',
            'tolerate': 'Fault Tolerance',
            'timing': 'Timing',
            'arbitration': 'Arbitration'
        }
        
        for key, value in mapping.items():
            if key in category_lower:
                return value
        
        return ''
    
    def _determine_fsr_type(self, fsr_id: str) -> str:
        """Determine FSR type from ID."""
        
        type_mapping = {
            'AVD': 'Fault Avoidance',
            'DET': 'Fault Detection',
            'CTL': 'Fault Control',
            'SST': 'Safe State Transition',
            'TOL': 'Fault Tolerance',
            'WRN': 'Warning/Indication',
            'TIM': 'Timing',
            'ARB': 'Arbitration',
            'REA': 'Fault Reaction',
            'IND': 'Fault Indication',
            'MOD': 'Operating Mode',
            'RED': 'Functional Redundancy',
            'SEQ': 'Sequence Control',
            'INT': 'Interface'
        }
        
        for code, name in type_mapping.items():
            if f'-{code}-' in fsr_id:
                return name
        
        return 'General'