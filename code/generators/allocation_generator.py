# generators/allocation_generator.py
# Business logic for allocating FSRs to architectural elements per ISO 26262-3:2018, Clause 7.4.2.8
# IMPROVED VERSION - Following FSR Generator Pattern

from typing import List, Dict, Optional, Callable, Tuple
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import FunctionalSafetyRequirement, SafetyGoal
from core.constants import AllocationType
from cat.log import log


class AllocationGenerator:
    """
    Allocates Functional Safety Requirements to architectural elements.
    Per ISO 26262-3:2018, Clause 7.4.2.8
    
    - Allocates FSRs to system elements
    - Maintains ASIL integrity (7.4.2.8.a)
    - Considers freedom from interference (7.4.2.8.b)
    - Defines interfaces (7.4.2.8.c)
    """
    
    def __init__(self, llm_function: Callable[[str], str]):
        """
        Initialize allocation generator.
        
        Args:
            llm_function: Function that takes a prompt string and returns LLM response
        """
        self.llm = llm_function
    
    def allocate_fsrs(self, fsrs: List[FunctionalSafetyRequirement],
                     safety_goals: List[SafetyGoal],
                     system_name: str = "the system") -> List[FunctionalSafetyRequirement]:
        """
        Allocate all FSRs to architectural elements.
        
        Args:
            fsrs: List of FSR objects (may have preliminary allocations)
            safety_goals: List of SafetyGoal objects for context
            system_name: Name of the system
            
        Returns:
            List of FSR objects with updated allocation information
        """
        log.info("🏗️ Starting FSR allocation to architectural elements")
        log.info(f"📊 System: {system_name}")
        log.info(f"📋 FSRs to allocate: {len(fsrs)}")
        log.info(f"🎯 Safety goals: {len(safety_goals)}")
        
        # Build prompt
        prompt = self._build_allocation_prompt(fsrs, safety_goals, system_name)
        
        # Get LLM response
        try:
            log.info("🤖 Calling LLM for allocation...")
            response = self.llm(prompt)
            
            log.info(f"📥 Received LLM response ({len(response)} chars)")
            log.info("=" * 80)
            log.info("LLM RESPONSE PREVIEW:")
            log.info(response[:1000] if len(response) > 1000 else response)
            log.info("=" * 80)
            
            # Parse allocations with multiple strategies
            allocations = self._parse_allocations(response, fsrs)
            
            if not allocations:
                log.warning("⚠️ No allocations parsed from LLM response")
                return fsrs
            
            log.info(f"✅ Successfully parsed {len(allocations)} allocations")
            
            # Update FSRs with allocation information
            updated_count = 0
            for fsr in fsrs:
                if fsr.id in allocations:
                    alloc = allocations[fsr.id]
                    fsr.allocated_to = alloc['primary_component']
                    fsr.allocation_type = alloc['component_type']
                    fsr.allocation_rationale = alloc['rationale']
                    fsr.interface = alloc.get('interface', 'To be specified in detailed design')
                    updated_count += 1
                    log.info(f"✅ Allocated {fsr.id} → {fsr.allocated_to}")
                else:
                    log.warning(f"⚠️ No allocation found for {fsr.id}")
            
            log.info(f"✅ Allocation complete: {updated_count}/{len(fsrs)} FSRs allocated")
            
            return fsrs
            
        except Exception as e:
            log.error(f"❌ Error allocating FSRs: {e}")
            import traceback
            log.error(traceback.format_exc())
            return fsrs
    
    def allocate_single_fsr(self, fsr: FunctionalSafetyRequirement,
                           component: str) -> FunctionalSafetyRequirement:
        """
        Allocate a single FSR to a specific component (manual allocation).
        
        Args:
            fsr: FSR to allocate
            component: Target component name
            
        Returns:
            Updated FSR object
        """
        log.info(f"🎯 Manual allocation: {fsr.id} → {component}")
        
        # Determine component type
        component_type = self._determine_component_type(component)
        
        # Update FSR
        fsr.allocated_to = component
        fsr.allocation_type = component_type
        fsr.allocation_rationale = f"Manually allocated to {component}"
        fsr.interface = "To be specified in detailed design"
        
        log.info(f"✅ Allocated {fsr.id} to {component} ({component_type})")
        
        return fsr
    
    def _build_allocation_prompt(self, fsrs: List[FunctionalSafetyRequirement],
                                safety_goals: List[SafetyGoal],
                                system_name: str) -> str:
        """
        Build LLM prompt for FSR allocation.
        
        Args:
            fsrs: List of FSR objects
            safety_goals: List of SafetyGoal objects
            system_name: System name
            
        Returns:
            Prompt string
        """
        prompt = f"""You are allocating Functional Safety Requirements (FSRs) to system components per ISO 26262-3:2018, Clause 7.4.2.8.

**System:** {system_name}
**FSRs to Allocate:** {len(fsrs)}

**CRITICAL: You MUST use this EXACT format for each allocation:**

```
---
## Allocation for FSR: FSR-SG-001-DET-1
**Primary Allocation:** Battery Voltage Sensor
- **Component Type:** Hardware
- **Rationale:** Hardware sensor provides direct voltage measurement with high reliability required for ASIL C
- **Interface:** Analog voltage signal to microcontroller ADC, I2C diagnostic interface
---
```

**ISO 26262-3:2018, 7.4.2.8 Requirements:**

a) ASIL shall be inherited from safety goal (or decomposed per ISO 26262-9)
b) Freedom from interference shall be considered
c) Interface specifications shall be defined for multiple E/E systems

**Allocation Guidelines:**

1. **Functional Capability**
   - Which component can best implement this requirement?
   - Hardware vs Software considerations
   - Feasibility and performance

2. **ASIL Considerations**
   - Component must support required ASIL level
   - Hardware often preferred for ASIL C/D detection
   - Software may be suitable for ASIL A/B with proper measures

3. **System Architecture**
   - Consider existing system components
   - Minimize interface complexity
   - Group related FSRs to same component when logical

4. **Freedom from Interference**
   - Higher ASIL functions protected from lower ASIL
   - Spatial and temporal independence
   - Resource allocation and partitioning

**Component Types to Consider:**

**Hardware:**
- Sensors: voltage, current, temperature, position, speed, pressure
- Actuators: motors, valves, relays, solenoids
- ECU Hardware: microcontroller, memory, power supply, watchdog
- Safety Circuits: voltage monitor, current monitor, safety relay
- Redundant channels

**Software:**
- Diagnostic modules
- Control algorithms
- Fault handlers
- State machines
- HMI/warning systems
- Protocol handlers

**External Systems:**
- Vehicle Control Unit (VCU)
- Body Control Module (BCM)
- Gateway/Communication module
- HMI display
- Cloud services

**Mechanical:**
- Fail-safe mechanisms
- Spring-return actuators
- Mechanical locks

**FSRs to Allocate:**

"""
        
        for fsr in fsrs:
            prompt += f"""
### {fsr.id}
- **Description:** {fsr.description}
- **Type:** {fsr.type}
- **ASIL:** {fsr.asil}
- **Safety Goal:** {fsr.safety_goal_id}
- **Current Allocation:** {fsr.allocated_to if fsr.allocated_to else 'Not specified'}

"""
        
        prompt += """
**Requirements:**
- Use the EXACT format shown above (starting with --- and ending with ---)
- Each FSR must have exactly ONE primary allocation
- Provide clear technical rationale for each allocation
- Consider ASIL requirements in allocation decisions
- Document key interfaces between components
- Group related FSRs logically when appropriate
- Ensure freedom from interference for different ASIL levels

**Start allocating all FSRs now. Remember: Use the exact format with --- delimiters!**
"""
        
        return prompt
    
    def _parse_allocations(self, llm_response: str,
                          fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Parse allocation information from LLM response with multiple strategies.
        
        Args:
            llm_response: LLM output text
            fsrs: List of FSR objects for reference
            
        Returns:
            Dictionary mapping FSR ID to allocation information
        """
        log.info("🔍 Starting allocation parsing")
        
        # Strategy 1: Structured text format (primary)
        allocations = self._parse_from_structured_text(llm_response, fsrs)
        if allocations:
            log.info(f"✅ Parsed {len(allocations)} allocations from structured text")
            return allocations
        
        # Strategy 2: Section-based parsing (fallback)
        log.info("Trying section-based parser")
        allocations = self._parse_from_sections(llm_response, fsrs)
        if allocations:
            log.info(f"✅ Parsed {len(allocations)} allocations from sections")
            return allocations
        
        # Strategy 3: Regex extraction (aggressive last resort)
        log.info("Trying regex extraction parser")
        allocations = self._parse_with_regex(llm_response, fsrs)
        if allocations:
            log.info(f"✅ Parsed {len(allocations)} allocations with regex")
            return allocations
        
        log.error("❌ All parsing strategies failed")
        return {}
    
    def _parse_from_structured_text(self, response: str,
                                    fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Parse allocations from structured text format (primary strategy).
        
        Expected format:
        ---
        ## Allocation for FSR: FSR-ID
        **Primary Allocation:** Component Name
        - **Component Type:** Type
        - **Rationale:** Reason
        - **Interface:** Interface description
        ---
        """
        allocations = {}
        lines = response.split('\n')
        
        current_fsr_id = None
        current_allocation = {}
        in_allocation_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Start of allocation block
            if line_stripped == '---':
                if current_fsr_id and current_allocation and 'primary_component' in current_allocation:
                    # Save previous allocation
                    allocations[current_fsr_id] = current_allocation
                    log.info(f"Parsed allocation for {current_fsr_id}")
                
                # Toggle block state
                in_allocation_block = not in_allocation_block
                current_fsr_id = None
                current_allocation = {}
                continue
            
            if not in_allocation_block:
                continue
            
            # Detect FSR ID
            if line_stripped.startswith('## Allocation for FSR:'):
                # Extract FSR ID
                for fsr in fsrs:
                    if fsr.id in line_stripped:
                        current_fsr_id = fsr.id
                        current_allocation = {
                            'fsr_id': fsr.id,
                            'primary_component': '',
                            'component_type': 'Unknown',
                            'rationale': '',
                            'interface': ''
                        }
                        break
            
            # Parse allocation fields
            elif current_fsr_id:
                if line_stripped.startswith('**Primary Allocation:**'):
                    current_allocation['primary_component'] = line_stripped.replace('**Primary Allocation:**', '').strip()
                elif line_stripped.startswith('- **Component Type:**'):
                    comp_type = line_stripped.replace('- **Component Type:**', '').strip()
                    current_allocation['component_type'] = comp_type
                elif line_stripped.startswith('- **Rationale:**'):
                    rationale = line_stripped.replace('- **Rationale:**', '').strip()
                    current_allocation['rationale'] = rationale
                elif line_stripped.startswith('- **Interface:**'):
                    interface = line_stripped.replace('- **Interface:**', '').strip()
                    current_allocation['interface'] = interface
        
        # Save last allocation
        if current_fsr_id and current_allocation and 'primary_component' in current_allocation:
            allocations[current_fsr_id] = current_allocation
        
        return allocations
    
    def _parse_from_sections(self, response: str,
                            fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Parse allocations from section-based format (fallback strategy).
        
        Looks for sections starting with ## and containing FSR IDs.
        """
        allocations = {}
        lines = response.split('\n')
        
        current_fsr_id = None
        current_section = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # New section header
            if line_stripped.startswith('##'):
                # Process previous section
                if current_fsr_id and current_section:
                    allocation = self._extract_allocation_from_section(
                        current_fsr_id, current_section
                    )
                    if allocation:
                        allocations[current_fsr_id] = allocation
                        log.info(f"Extracted allocation for {current_fsr_id} from section")
                
                # Start new section
                current_section = [line]
                current_fsr_id = None
                
                # Find FSR ID in header
                for fsr in fsrs:
                    if fsr.id in line_stripped:
                        current_fsr_id = fsr.id
                        break
            else:
                current_section.append(line)
        
        # Process last section
        if current_fsr_id and current_section:
            allocation = self._extract_allocation_from_section(
                current_fsr_id, current_section
            )
            if allocation:
                allocations[current_fsr_id] = allocation
        
        return allocations
    
    def _extract_allocation_from_section(self, fsr_id: str, 
                                        section_lines: List[str]) -> Optional[Dict]:
        """Extract allocation info from a section of text."""
        section_text = '\n'.join(section_lines)
        
        allocation = {
            'fsr_id': fsr_id,
            'primary_component': '',
            'component_type': 'Unknown',
            'rationale': '',
            'interface': ''
        }
        
        # Look for component name (usually after "Allocation:" or "Component:")
        component_patterns = [
            r'Primary Allocation[:\s]+([^\n]+)',
            r'Allocated to[:\s]+([^\n]+)',
            r'Component[:\s]+([^\n]+)',
        ]
        
        for pattern in component_patterns:
            match = re.search(pattern, section_text, re.IGNORECASE)
            if match:
                allocation['primary_component'] = match.group(1).strip()
                break
        
        # Look for component type
        type_match = re.search(r'Component Type[:\s]+([^\n]+)', section_text, re.IGNORECASE)
        if type_match:
            allocation['component_type'] = type_match.group(1).strip()
        
        # Look for rationale
        rationale_match = re.search(r'Rationale[:\s]+([^\n]+)', section_text, re.IGNORECASE)
        if rationale_match:
            allocation['rationale'] = rationale_match.group(1).strip()
        
        # Look for interface
        interface_match = re.search(r'Interface[:\s]+([^\n]+)', section_text, re.IGNORECASE)
        if interface_match:
            allocation['interface'] = interface_match.group(1).strip()
        
        # Only return if we found at least a component name
        if allocation['primary_component']:
            return allocation
        
        return None
    
    def _parse_with_regex(self, response: str,
                         fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Aggressive regex-based extraction as last resort.
        
        Looks for any mention of FSR IDs and tries to find associated component names.
        """
        allocations = {}
        
        log.info("🔍 Starting aggressive regex parsing")
        
        for fsr in fsrs:
            # Find FSR ID in text
            pattern = re.escape(fsr.id) + r'[^\n]*'
            matches = re.finditer(pattern, response)
            
            for match in matches:
                # Get context around FSR ID (next 5 lines)
                start_pos = match.start()
                context_text = response[start_pos:start_pos + 500]
                
                # Look for component indicators
                component_patterns = [
                    r'(?:allocated to|assign to|component|element)[:\s]+([A-Z][A-Za-z\s]{3,40})',
                    r'(?:hardware|software|sensor|monitor|controller|module)[:\s]+([A-Z][A-Za-z\s]{3,40})',
                ]
                
                component_name = None
                for pattern in component_patterns:
                    comp_match = re.search(pattern, context_text, re.IGNORECASE)
                    if comp_match:
                        component_name = comp_match.group(1).strip()
                        # Clean up
                        component_name = component_name.split('\n')[0]
                        component_name = component_name.split(',')[0]
                        if len(component_name) > 5:  # Reasonable name length
                            break
                
                if component_name:
                    allocations[fsr.id] = {
                        'fsr_id': fsr.id,
                        'primary_component': component_name,
                        'component_type': self._determine_component_type(component_name),
                        'rationale': f"Extracted from LLM response for {fsr.id}",
                        'interface': 'To be specified'
                    }
                    log.info(f"Regex extracted: {fsr.id} → {component_name}")
                    break  # Found allocation, move to next FSR
        
        return allocations
    
    def _determine_component_type(self, component: str) -> str:
        """
        Determine component type from component name.
        
        Args:
            component: Component name
            
        Returns:
            Component type string
        """
        component_lower = component.lower()
        
        # Hardware keywords
        if any(word in component_lower for word in [
            'hardware', 'sensor', 'actuator', 'ecu', 'module', 
            'circuit', 'monitor', 'controller', 'relay', 'valve',
            'motor', 'microcontroller', 'watchdog', 'voltage', 'current',
            'temperature', 'pressure', 'speed', 'position'
        ]):
            return AllocationType.HARDWARE.value
        
        # Software keywords
        elif any(word in component_lower for word in [
            'software', 'algorithm', 'function', 'logic', 'routine',
            'application', 'driver', 'handler', 'protocol', 'stack',
            'diagnostic', 'fault', 'state machine'
        ]):
            return AllocationType.SOFTWARE.value
        
        # External keywords
        elif any(word in component_lower for word in [
            'vcu', 'hmi', 'cluster', 'external', 'gateway', 'bcm',
            'vehicle', 'network', 'bus', 'cloud', 'display'
        ]):
            return AllocationType.EXTERNAL.value
        
        # Mechanical keywords
        elif any(word in component_lower for word in [
            'mechanical', 'spring', 'lock', 'physical', 'fail-safe'
        ]):
            return AllocationType.MECHANICAL.value
        
        else:
            return AllocationType.HARDWARE.value  # Default


class AllocationAnalyzer:
    """Helper class for analyzing allocation results"""
    
    @staticmethod
    def get_allocation_statistics(fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Generate statistics about FSR allocations.
        
        Args:
            fsrs: List of FSR objects
            
        Returns:
            Dictionary with allocation statistics
        """
        stats = {
            'total_fsrs': len(fsrs),
            'allocated': 0,
            'unallocated': 0,
            'by_component': {},
            'by_component_type': {},
            'by_asil': {},
            'by_type': {}
        }
        
        for fsr in fsrs:
            # Allocation status
            if fsr.is_allocated():
                stats['allocated'] += 1
                
                # By component
                comp = fsr.allocated_to
                if comp not in stats['by_component']:
                    stats['by_component'][comp] = {
                        'count': 0,
                        'asil_levels': set(),
                        'fsr_ids': []
                    }
                stats['by_component'][comp]['count'] += 1
                stats['by_component'][comp]['asil_levels'].add(fsr.asil)
                stats['by_component'][comp]['fsr_ids'].append(fsr.id)
                
                # By component type
                comp_type = fsr.allocation_type or 'Unknown'
                stats['by_component_type'][comp_type] = stats['by_component_type'].get(comp_type, 0) + 1
            else:
                stats['unallocated'] += 1
            
            # By ASIL
            stats['by_asil'][fsr.asil] = stats['by_asil'].get(fsr.asil, 0) + 1
            
            # By FSR type
            stats['by_type'][fsr.type] = stats['by_type'].get(fsr.type, 0) + 1
        
        return stats
    
    @staticmethod
    def format_allocation_matrix(fsrs: List[FunctionalSafetyRequirement]) -> str:
        """
        Format allocation matrix for display.
        
        Args:
            fsrs: List of FSR objects
            
        Returns:
            Formatted allocation matrix string
        """
        stats = AllocationAnalyzer.get_allocation_statistics(fsrs)
        
        matrix = "# FSR Allocation Matrix\n\n"
        matrix += f"**Total FSRs:** {stats['total_fsrs']}\n"
        matrix += f"**Allocated:** {stats['allocated']}\n"
        matrix += f"**Unallocated:** {stats['unallocated']}\n\n"
        
        matrix += "## Allocation by Component\n\n"
        
        for component, info in sorted(stats['by_component'].items()):
            asil_str = ', '.join(sorted(info['asil_levels'], reverse=True))
            matrix += f"### {component}\n"
            matrix += f"- **FSR Count:** {info['count']}\n"
            matrix += f"- **ASIL Levels:** {asil_str}\n"
            matrix += f"- **FSRs:** {', '.join(info['fsr_ids'][:5])}"
            if len(info['fsr_ids']) > 5:
                matrix += f" ... and {len(info['fsr_ids']) - 5} more"
            matrix += "\n\n"
        
        matrix += "## Allocation by Type\n\n"
        
        for comp_type, count in sorted(stats['by_component_type'].items()):
            percentage = (count / stats['allocated'] * 100) if stats['allocated'] > 0 else 0
            matrix += f"- **{comp_type}:** {count} FSRs ({percentage:.1f}%)\n"
        
        return matrix
    
    @staticmethod
    def validate_allocation(fsrs: List[FunctionalSafetyRequirement]) -> Tuple[bool, List[str]]:
        """
        Validate allocation completeness and correctness.
        
        Args:
            fsrs: List of FSR objects
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check: All FSRs allocated
        unallocated = [f for f in fsrs if not f.is_allocated()]
        if unallocated:
            issues.append(f"{len(unallocated)} FSRs not allocated: {', '.join([f.id for f in unallocated[:5]])}")
        
        # Check: No placeholder allocations
        placeholder_terms = ['tbd', 'to be determined', 'unknown', 'placeholder', 'not specified']
        placeholders = [f for f in fsrs if f.allocated_to and any(term in f.allocated_to.lower() for term in placeholder_terms)]
        if placeholders:
            issues.append(f"{len(placeholders)} FSRs have placeholder allocations")
        
        # Check: Rationale provided
        no_rationale = [f for f in fsrs if f.is_allocated() and not f.allocation_rationale]
        if no_rationale:
            issues.append(f"{len(no_rationale)} FSRs lack allocation rationale")
        
        is_valid = len(issues) == 0
        return is_valid, issues