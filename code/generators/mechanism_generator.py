# generators/mechanism_generator.py
# Business logic for identifying safety mechanisms per ISO 26262-4:2018, Clause 6.4.5.4

from typing import List, Dict, Optional, Callable
import re
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import (
    FunctionalSafetyRequirement,
    SafetyGoal,
    SafetyMechanism,
    MechanismFSRMapping
)


class MechanismGenerator:
    """
    Generates safety mechanisms for FSRs and maps them to requirements.
    Per ISO 26262-4:2018, Clause 6.4.5.4
    
    Safety mechanisms are technical solutions to:
    - Detect faults
    - Control malfunctions
    - Achieve/maintain safe state
    - Provide fault tolerance
    """
    
    def __init__(self, llm_function: Callable[[str], str], catalog_path: Optional[str] = None):
        """
        Initialize mechanism generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
            catalog_path: Path to safety_mechanisms_catalog.json
        """
        self.llm = llm_function
        self.catalog = self._load_catalog(catalog_path) if catalog_path else None
    
    def _load_catalog(self, catalog_path: str) -> Optional[Dict]:
        """Load safety mechanisms catalog from JSON file"""
        if not os.path.exists(catalog_path):
            return None
        
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def generate_mechanisms_for_fsrs(self,
                                    fsrs: List[FunctionalSafetyRequirement],
                                    safety_goals: List[SafetyGoal],
                                    system_name: str = "the system") -> tuple[List[SafetyMechanism], List[MechanismFSRMapping]]:
        """
        Generate safety mechanisms for all FSRs.
        
        Args:
            fsrs: List of FSR objects
            safety_goals: List of SafetyGoal objects
            system_name: Name of the system
            
        Returns:
            Tuple of (mechanisms list, mappings list)
        """
        # Build prompt
        prompt = self._build_mechanism_prompt(fsrs, safety_goals, system_name)
        
        # Get LLM response
        try:
            response = self.llm(prompt)
            
            # Parse mechanisms and mappings
            mechanisms, mappings = self._parse_mechanisms(response, fsrs)
            
            return mechanisms, mappings
            
        except Exception as e:
            print(f"Error generating mechanisms: {e}")
            return [], []
    
    def generate_mechanisms_for_fsr(self,
                                   fsr: FunctionalSafetyRequirement,
                                   safety_goal: SafetyGoal,
                                   system_name: str = "the system") -> tuple[List[SafetyMechanism], MechanismFSRMapping]:
        """
        Generate safety mechanisms for a single FSR.
        
        Args:
            fsr: FSR object
            safety_goal: Related SafetyGoal object
            system_name: Name of the system
            
        Returns:
            Tuple of (mechanisms list, mapping)
        """
        # Build prompt for single FSR
        prompt = self._build_single_fsr_mechanism_prompt(fsr, safety_goal, system_name)
        
        try:
            response = self.llm(prompt)
            
            # Parse mechanisms
            mechanisms, mappings = self._parse_mechanisms(response, [fsr])
            
            mapping = mappings[0] if mappings else MechanismFSRMapping(fsr_id=fsr.id)
            
            return mechanisms, mapping
            
        except Exception as e:
            print(f"Error generating mechanisms for {fsr.id}: {e}")
            return [], MechanismFSRMapping(fsr_id=fsr.id)
    
    def _build_mechanism_prompt(self,
                               fsrs: List[FunctionalSafetyRequirement],
                               safety_goals: List[SafetyGoal],
                               system_name: str) -> str:
        """Build LLM prompt for mechanism generation"""
        
        prompt = f"""You are an ISO 26262 Functional Safety expert identifying Safety Mechanisms.

**System:** {system_name}
**Task:** Identify appropriate safety mechanisms for each FSR below.

**ISO 26262-4:2018, Clause 6.4.5.4 Requirements:**
- Safety mechanisms shall detect/control faults to maintain safe state
- Mechanisms shall be suitable for the allocated ASIL
- Diagnostic coverage shall be specified
- Multiple mechanisms may be combined

**Safety Mechanism Categories:**

1. **Diagnostic Mechanisms** (Detection)
   - Plausibility checks (range, gradient, correlation)
   - Checksums & CRCs
   - Built-in self-test (BIST)
   - Watchdog timers
   - Parity/ECC for memory
   - Signature analysis

2. **Redundancy Mechanisms** (Fault Tolerance)
   - Dual/triple channel redundancy
   - Voting (2oo3, 1oo2D, etc.)
   - Diverse redundancy
   - Backup sensors/actuators
   - Independent monitoring channels

3. **Safe State Mechanisms** (Control & Reaction)
   - Controlled shutdown sequences
   - Safe state transition logic
   - Default fail-safe positions
   - Degraded mode operation
   - Emergency operation modes

4. **Supervision Mechanisms** (Monitoring)
   - Execution time monitoring
   - Deadline supervision
   - Alive/heartbeat monitoring
   - Control flow monitoring
   - Stack overflow detection

5. **Communication Protection** (Data Integrity)
   - CRC/checksum on messages
   - Sequence counters
   - Message timeouts
   - Source authentication
   - Duplicate message detection

"""
        
        # Add FSRs context
        prompt += f"\n**Functional Safety Requirements ({len(fsrs)} FSRs):**\n\n"
        
        for fsr in fsrs[:50]:  # Limit to first 50 to avoid token limits
            sg = next((g for g in safety_goals if g.id == fsr.safety_goal_id), None)
            
            prompt += f"---\n"
            prompt += f"**FSR-ID:** {fsr.id}\n"
            prompt += f"**Type:** {fsr.type}\n"
            prompt += f"**ASIL:** {fsr.asil}\n"
            prompt += f"**Description:** {fsr.description}\n"
            if sg:
                prompt += f"**Safety Goal:** {sg.description}\n"
                prompt += f"**Safe State:** {sg.safe_state}\n"
            prompt += "\n"
        
        prompt += """
**Response Format:**

For each FSR, provide safety mechanisms in this EXACT format:

```
### FSR: {FSR-ID}

**MECHANISM-1:**
ID: SM-{FSR-ID}-001
Name: {Mechanism name}
Type: {diagnostic|redundancy|safe_state|supervision|communication}
Description: {2-3 sentence description of how the mechanism works}
ASIL Suitability: {A, B, C, D}
Diagnostic Coverage: {percentage or High/Medium/Low}
Detection Capability: {What faults are detected}
Implementation Notes: {Key considerations}

**MECHANISM-2:**
ID: SM-{FSR-ID}-002
...

**COVERAGE RATIONALE:**
{Explain how these mechanisms provide adequate coverage for the FSR}

**RESIDUAL RISK:**
{Describe any remaining risks not covered by mechanisms}

---
```

**CRITICAL INSTRUCTIONS:**
1. For DETECTION FSRs: Focus on diagnostic and supervision mechanisms
2. For CONTROL/REACTION FSRs: Focus on safe state mechanisms
3. For TOLERANCE FSRs: Focus on redundancy mechanisms
4. Each FSR should have 2-4 mechanisms depending on ASIL
5. Higher ASIL requires more comprehensive mechanisms
6. Mechanisms must be appropriate for the FSR type and ASIL level

Now analyze each FSR and identify appropriate safety mechanisms:
"""
        
        return prompt
    
    def _build_single_fsr_mechanism_prompt(self,
                                          fsr: FunctionalSafetyRequirement,
                                          safety_goal: SafetyGoal,
                                          system_name: str) -> str:
        """Build LLM prompt for single FSR mechanism generation"""
        
        prompt = f"""You are an ISO 26262 Functional Safety expert identifying Safety Mechanisms.

**System:** {system_name}
**Task:** Identify safety mechanisms for this specific FSR.

**FSR Details:**
- **ID:** {fsr.id}
- **Type:** {fsr.fsr_type}
- **ASIL:** {fsr.asil}
- **Description:** {fsr.description}
- **Verification Method:** {fsr.verification_method}

**Related Safety Goal:**
- **ID:** {safety_goal.id}
- **Description:** {safety_goal.description}
- **Safe State:** {safety_goal.safe_state}
- **FTTI:** {safety_goal.ftti}

**Available Mechanism Categories:**
1. Diagnostic (detection, BIST, checks)
2. Redundancy (dual channel, voting)
3. Safe State (shutdown, degraded mode)
4. Supervision (watchdogs, monitoring)
5. Communication (CRC, timeouts)

Identify 2-4 appropriate mechanisms for this FSR. Use the format from the general prompt.
"""
        
        return prompt
    
    def _parse_mechanisms(self, response: str,
                         fsrs: List[FunctionalSafetyRequirement]) -> tuple[List[SafetyMechanism], List[MechanismFSRMapping]]:
        """
        Parse safety mechanisms from LLM response.
        
        Returns:
            Tuple of (mechanisms, mappings)
        """
        mechanisms = []
        mappings = []
        
        # Split by FSR sections
        fsr_sections = re.split(r'### FSR:', response)
        
        for section in fsr_sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # Extract FSR ID
            fsr_id_match = re.search(r'(FSR-[A-Z0-9-]+)', lines[0])
            if not fsr_id_match:
                continue
            
            fsr_id = fsr_id_match.group(1)
            
            # Find the FSR object
            fsr = next((f for f in fsrs if f.id == fsr_id), None)
            if not fsr:
                continue
            
            # Parse mechanisms for this FSR
            fsr_mechanisms = self._parse_fsr_mechanisms(section, fsr_id)
            mechanisms.extend(fsr_mechanisms)
            
            # Parse coverage rationale and residual risk
            coverage_rationale = self._extract_section(section, "COVERAGE RATIONALE")
            residual_risk = self._extract_section(section, "RESIDUAL RISK")
            
            # Create mapping
            mapping = MechanismFSRMapping(
                fsr_id=fsr_id,
                mechanism_ids=[m.id for m in fsr_mechanisms],
                coverage_rationale=coverage_rationale,
                residual_risk=residual_risk
            )
            mappings.append(mapping)
        
        return mechanisms, mappings
    
    def _parse_fsr_mechanisms(self, section: str, fsr_id: str) -> List[SafetyMechanism]:
        """Parse individual mechanisms from an FSR section"""
        mechanisms = []
        
        # Split by MECHANISM markers
        mech_sections = re.split(r'\*\*MECHANISM-\d+:\*\*', section)
        
        for mech_section in mech_sections[1:]:  # Skip first part (before mechanisms)
            mechanism = self._parse_single_mechanism(mech_section, fsr_id)
            if mechanism:
                mechanisms.append(mechanism)
        
        return mechanisms
    
    def _parse_single_mechanism(self, text: str, fsr_id: str) -> Optional[SafetyMechanism]:
        """Parse a single mechanism from text"""
        lines = text.strip().split('\n')
        
        mech_data = {}
        current_field = None
        current_value = []
        
        for line in lines:
            line = line.strip()
            
            # Check if line starts a new field
            if ':' in line and not line.startswith('**COVERAGE') and not line.startswith('**RESIDUAL'):
                if current_field and current_value:
                    mech_data[current_field] = ' '.join(current_value).strip()
                
                parts = line.split(':', 1)
                current_field = parts[0].strip().lower().replace(' ', '_')
                current_value = [parts[1].strip()] if len(parts) > 1 else []
            elif current_field:
                current_value.append(line)
        
        # Save last field
        if current_field and current_value:
            mech_data[current_field] = ' '.join(current_value).strip()
        
        # Create mechanism object
        if 'id' not in mech_data or 'name' not in mech_data:
            return None
        
        # Parse ASIL suitability
        asil_text = mech_data.get('asil_suitability', '')
        asil_list = [a.strip() for a in re.findall(r'[ABCD]', asil_text)]
        
        mechanism = SafetyMechanism(
            id=mech_data.get('id', f'SM-{fsr_id}-X'),
            name=mech_data.get('name', 'Unnamed Mechanism'),
            mechanism_type=mech_data.get('type', 'diagnostic'),
            description=mech_data.get('description', ''),
            applicable_fsrs=[fsr_id],
            asil_suitability=asil_list,
            diagnostic_coverage=mech_data.get('diagnostic_coverage', ''),
            implementation_notes=mech_data.get('implementation_notes', ''),
            verification_method=mech_data.get('verification_method', ''),
            detection_capability=mech_data.get('detection_capability', ''),
            reaction_time=mech_data.get('reaction_time', ''),
            independence_level=mech_data.get('independence_level', '')
        )
        
        return mechanism
    
    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract content of a named section from text"""
        pattern = rf'\*\*{section_name}:\*\*\s*\n(.*?)(?=\*\*[A-Z]|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""


class MechanismFormatter:
    """Helper class for formatting safety mechanism output"""
    
    @staticmethod
    def format_mechanisms_summary(mechanisms: List[SafetyMechanism],
                                  mappings: List[MechanismFSRMapping],
                                  fsrs: List[FunctionalSafetyRequirement],
                                  system_name: str) -> str:
        """Format mechanisms into readable summary"""
        
        output = f"""✅ **Safety Mechanisms Identified for {system_name}**

**ISO 26262-4:2018, Clause 6.4.5.4 Compliance:**
Safety mechanisms specified to detect, control, and tolerate faults.

---

"""
        
        # Statistics
        mech_by_type = {}
        for m in mechanisms:
            mech_by_type[m.mechanism_type] = mech_by_type.get(m.mechanism_type, 0) + 1
        
        output += "**📊 Mechanism Statistics:**\n\n"
        output += f"- **Total Mechanisms:** {len(mechanisms)}\n"
        output += f"- **FSRs Covered:** {len(mappings)}/{len(fsrs)}\n"
        output += "\n**By Type:**\n"
        for mtype, count in mech_by_type.items():
            output += f"- {mtype.title()}: {count}\n"
        
        output += "\n---\n\n"
        
        # Mechanism details by FSR
        output += "**🔧 Identified Safety Mechanisms:**\n\n"
        
        for mapping in mappings:
            fsr = next((f for f in fsrs if f.id == mapping.fsr_id), None)
            if not fsr:
                continue
            
            output += f"### {mapping.fsr_id}: {fsr.fsr_type}\n\n"
            output += f"**Requirement:** {fsr.description[:100]}...\n"
            output += f"**ASIL:** {fsr.asil}\n\n"
            
            # List mechanisms
            for mech_id in mapping.mechanism_ids:
                mech = next((m for m in mechanisms if m.id == mech_id), None)
                if not mech:
                    continue
                
                output += f"**{mech.name}** (`{mech.id}`)\n"
                output += f"- **Type:** {mech.get_mechanism_category()}\n"
                output += f"- **Description:** {mech.description}\n"
                output += f"- **Coverage:** {mech.diagnostic_coverage}\n"
                output += f"- **ASIL:** {', '.join(mech.asil_suitability)}\n"
                output += "\n"
            
            if mapping.coverage_rationale:
                output += f"**Coverage Rationale:** {mapping.coverage_rationale}\n\n"
            
            if mapping.residual_risk:
                output += f"⚠️ **Residual Risk:** {mapping.residual_risk}\n\n"
            
            output += "---\n\n"
        
        return output