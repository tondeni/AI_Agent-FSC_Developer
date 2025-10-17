"""
FSC Content Helpers - No external dependencies
Pure dictionary operations for FSC structured content
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

# Schema version - increment when changing structure
FSC_SCHEMA_VERSION = "1.0"


def create_fsr_dict(
    id: str,
    description: str,
    type: str,
    asil: str,
    safety_goal_id: str,
    safe_state: str,
    ftti: str,
    validation_criteria: List[str],
    verification_method: str,
    allocated_to: Optional[str] = None,
    operating_modes: str = "All modes"
) -> Dict:
    """
    Create FSR dictionary conforming to contract.
    No classes, just dictionaries.
    """
    return {
        'id': id,
        'description': description,
        'type': type,
        'asil': asil,
        'safety_goal_id': safety_goal_id,
        'safe_state': safe_state,
        'ftti': ftti,
        'validation_criteria': validation_criteria,
        'verification_method': verification_method,
        'allocated_to': allocated_to,
        'operating_modes': operating_modes
    }


def create_safety_mechanism_dict(
    id: str,
    name: str,
    description: str,
    type: str,
    fsr_coverage: List[str],
    asil: str,
    implementation: str
) -> Dict:
    """Create Safety Mechanism dictionary conforming to contract."""
    return {
        'id': id,
        'name': name,
        'description': description,
        'type': type,
        'fsr_coverage': fsr_coverage,
        'asil': asil,
        'implementation': implementation
    }


def create_fsc_content_dict(
    system_name: str,
    introduction: str,
    safety_goal_summary: str,
    functional_safety_requirements: List[Dict],
    safety_mechanisms: List[Dict],
    architectural_allocation: str,
    verification_strategy: str
) -> Dict:
    """
    Create complete FSC content dictionary.
    This is what gets stored in cat.working_memory['fsc_structured_content']
    """
    return {
        'system_name': system_name,
        'introduction': introduction,
        'safety_goal_summary': safety_goal_summary,
        'functional_safety_requirements': functional_safety_requirements,
        'safety_mechanisms': safety_mechanisms,
        'architectural_allocation': architectural_allocation,
        'verification_strategy': verification_strategy,
        'metadata': {
            'generation_date': datetime.now().isoformat(),
            'generator_version': '0.1.0',
            'schema_version': FSC_SCHEMA_VERSION,
            'generator_plugin': 'FSC_Developer'
        }
    }


def validate_fsc_content(content: Dict) -> tuple[bool, List[str]]:
    """
    Validate FSC content dictionary against contract.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Required top-level keys
    required_keys = [
        'system_name', 'introduction', 'safety_goal_summary',
        'functional_safety_requirements', 'safety_mechanisms',
        'architectural_allocation', 'verification_strategy'
    ]
    
    for key in required_keys:
        if key not in content:
            errors.append(f"Missing required key: {key}")
    
    # Validate FSRs
    if 'functional_safety_requirements' in content:
        fsrs = content['functional_safety_requirements']
        if not isinstance(fsrs, list):
            errors.append("functional_safety_requirements must be a list")
        else:
            for i, fsr in enumerate(fsrs):
                if not isinstance(fsr, dict):
                    errors.append(f"FSR {i} must be a dictionary")
                    continue
                
                # Check required FSR fields
                fsr_required = ['id', 'description', 'type', 'asil', 'safety_goal_id']
                for field in fsr_required:
                    if field not in fsr:
                        errors.append(f"FSR {i} missing field: {field}")
    
    # Validate Safety Mechanisms
    if 'safety_mechanisms' in content:
        sms = content['safety_mechanisms']
        if not isinstance(sms, list):
            errors.append("safety_mechanisms must be a list")
        else:
            for i, sm in enumerate(sms):
                if not isinstance(sm, dict):
                    errors.append(f"SM {i} must be a dictionary")
                    continue
                
                sm_required = ['id', 'description', 'type', 'fsr_coverage']
                for field in sm_required:
                    if field not in sm:
                        errors.append(f"SM {i} missing field: {field}")
    
    return (len(errors) == 0, errors)


def get_fsc_statistics(content: Dict) -> Dict:
    """Calculate statistics from FSC content."""
    from collections import Counter
    
    fsrs = content.get('functional_safety_requirements', [])
    sms = content.get('safety_mechanisms', [])
    
    return {
        'total_fsrs': len(fsrs),
        'total_sms': len(sms),
        'asil_distribution': dict(Counter(fsr.get('asil', 'QM') for fsr in fsrs)),
        'fsr_types': dict(Counter(fsr.get('type', 'unknown') for fsr in fsrs)),
        'sm_types': dict(Counter(sm.get('type', 'unknown') for sm in sms)),
        'allocated_fsrs': len([fsr for fsr in fsrs if fsr.get('allocated_to')]),
        'unallocated_fsrs': len([fsr for fsr in fsrs if not fsr.get('allocated_to')])
    }


def format_fsc_summary(content: Dict) -> str:
    """Format FSC content as readable summary."""
    stats = get_fsc_statistics(content)
    
    output = f"""📊 **FSC Content Summary**

**System:** {content.get('system_name', 'Unknown')}

**Content:**
- FSRs: {stats['total_fsrs']}
- Safety Mechanisms: {stats['total_sms']}
- Allocated: {stats['allocated_fsrs']} / {stats['total_fsrs']} FSRs

**ASIL Distribution:**
"""
    
    for asil, count in sorted(stats['asil_distribution'].items()):
        output += f"  - ASIL {asil}: {count}\n"
    
    output += "\n**FSR Types:**\n"
    for fsr_type, count in stats['fsr_types'].items():
        output += f"  - {fsr_type}: {count}\n"
    
    return output