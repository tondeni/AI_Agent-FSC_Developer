# generators/allocation_generator.py
# Business logic for allocating FSRs to architectural elements per ISO 26262-3:2018, Clause 7.4.2.8

from typing import List, Dict, Optional, Callable, Tuple
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.models import FunctionalSafetyRequirement, SafetyGoal
from core.constants import AllocationType


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
        # Build prompt
        prompt = self._build_allocation_prompt(fsrs, safety_goals, system_name)
        
        # Get LLM response
        try:
            response = self.llm(prompt)
            
            # Parse allocations
            allocations = self._parse_allocations(response, fsrs)
            
            # Update FSRs with allocation information
            for fsr in fsrs:
                if fsr.id in allocations:
                    alloc = allocations[fsr.id]
                    fsr.allocated_to = alloc['primary_component']
                    fsr.allocation_type = alloc['component_type']
                    fsr.allocation_rationale = alloc['rationale']
                    fsr.interface = alloc.get('interface', 'To be specified in detailed design')
            
            return fsrs
            
        except Exception as e:
            print(f"Error allocating FSRs: {e}")
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
        # Determine component type
        component_type = self._determine_component_type(component)
        
        # Update FSR
        fsr.allocated_to = component
        fsr.allocation_type = component_type
        fsr.allocation_rationale = f"Manually allocated to {component}"
        fsr.interface = "To be specified in detailed design"
        
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

**ISO 26262-3:2018, 7.4.2.8 Requirements:**

a) ASIL shall be inherited from safety goal (or decomposed per ISO 26262-9)
b) Freedom from interference shall be considered
c) Interface specifications shall be defined for multiple E/E systems

**Your Task:**
For each FSR, determine the most appropriate component allocation based on:

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

**Typical Component Types:**

**Hardware Components:**
- Sensors (voltage, current, temperature, position, speed, pressure, etc.)
- Actuators and control elements (motors, valves, relays)
- ECU hardware (microcontroller, memory, power supply, communication)
- Safety monitoring circuits (watchdog, voltage monitor, current monitor)
- Redundant channels

**Software Components:**
- Diagnostic software modules
- Control algorithms and logic
- Fault handling routines
- State machines
- HMI/warning systems
- Communication protocol handlers

**External Systems:**
- Vehicle Control Unit (VCU)
- Body Control Module (BCM)
- Human-Machine Interface (HMI)
- Gateway/Communication module
- External monitoring systems
- Cloud services (if applicable)

**Mechanical Elements:**
- Physical fail-safe mechanisms
- Spring-return actuators
- Mechanical locks/interlocks

**Output Format:**

For each FSR, provide:

---
## Allocation for FSR: [FSR-ID]
**FSR:** [Brief description]
**Type:** [Detection/Control/Transition/etc.]
**ASIL:** [X]
**Linked to SG:** [SG-ID]

**Primary Allocation:** [Component Name]
- **Component Type:** [Hardware/Software/External/Mechanical]
- **Rationale:** [Why this component is appropriate - technical justification]
- **Interface:** [Key interfaces with other components]
- **Supporting Components:** [Other components involved, if any]

**Allocation Notes:**
- [ASIL considerations]
- [Freedom from interference measures]
- [Dependencies on other allocations]

---

**FSRs to Allocate:**

"""
        
        for fsr in fsrs:
            prompt += f"""
### {fsr.id}
- **Description:** {fsr.description}
- **Type:** {fsr.type}
- **ASIL:** {fsr.asil}
- **Linked to SG:** {fsr.safety_goal_id}
- **Preliminary Allocation:** {fsr.allocated_to if fsr.allocated_to else 'Not yet specified'}

"""
        
        prompt += """
**Requirements:**
- Each FSR must have exactly ONE primary allocation
- Provide clear technical rationale for each allocation
- Consider ASIL requirements in allocation decisions
- Document key interfaces between components
- Group related FSRs logically when appropriate
- Ensure freedom from interference for different ASIL levels

**Now allocate all FSRs to appropriate system components.**
"""
        
        return prompt
    
    def _parse_allocations(self, llm_response: str,
                          fsrs: List[FunctionalSafetyRequirement]) -> Dict:
        """
        Parse allocation information from LLM response.
        
        Args:
            llm_response: LLM output text
            fsrs: List of FSR objects for reference
            
        Returns:
            Dictionary mapping FSR ID to allocation information
        """
        allocations = {}
        current_fsr_id = None
        current_allocation = {}
        
        lines = llm_response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Detect FSR section
            if line.startswith('## Allocation for FSR:'):
                # Save previous allocation
                if current_fsr_id and current_allocation:
                    allocations[current_fsr_id] = current_allocation
                
                # Start new allocation
                for fsr in fsrs:
                    if fsr.id in line:
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
            if current_fsr_id:
                if line.startswith('**Primary Allocation:**'):
                    current_allocation['primary_component'] = line.replace('**Primary Allocation:**', '').strip()
                elif line.startswith('- **Component Type:**'):
                    comp_type = line.replace('- **Component Type:**', '').strip()
                    current_allocation['component_type'] = comp_type
                elif line.startswith('- **Rationale:**'):
                    rationale = line.replace('- **Rationale:**', '').strip()
                    current_allocation['rationale'] = rationale
                elif line.startswith('- **Interface:**'):
                    interface = line.replace('- **Interface:**', '').strip()
                    current_allocation['interface'] = interface
        
        # Save last allocation
        if current_fsr_id and current_allocation:
            allocations[current_fsr_id] = current_allocation
        
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
            'motor', 'microcontroller', 'watchdog'
        ]):
            return AllocationType.HARDWARE.value
        
        # Software keywords
        elif any(word in component_lower for word in [
            'software', 'algorithm', 'function', 'logic', 'routine',
            'application', 'driver', 'handler', 'protocol', 'stack'
        ]):
            return AllocationType.SOFTWARE.value
        
        # External keywords
        elif any(word in component_lower for word in [
            'vcu', 'hmi', 'cluster', 'external', 'gateway', 'bcm',
            'vehicle', 'network', 'bus', 'cloud'
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
        
        # Check: ASIL integrity (warning if different from parent)
        # This is just a check, not an error, as ASIL decomposition may be valid
        
        # Check: No placeholder allocations
        placeholder_terms = ['tbd', 'to be determined', 'unknown', 'placeholder']
        placeholders = [f for f in fsrs if any(term in f.allocated_to.lower() for term in placeholder_terms)]
        if placeholders:
            issues.append(f"{len(placeholders)} FSRs have placeholder allocations")
        
        # Check: Rationale provided
        no_rationale = [f for f in fsrs if f.is_allocated() and not f.allocation_rationale]
        if no_rationale:
            issues.append(f"{len(no_rationale)} FSRs lack allocation rationale")
        
        is_valid = len(issues) == 0
        return is_valid, issues