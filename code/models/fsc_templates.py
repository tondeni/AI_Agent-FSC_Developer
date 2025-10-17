"""
FSC Content Templates with LLM Prompts and Weights
Defines structured generation for each FSC section
"""
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class SectionTemplate:
    """Template for a single FSC section"""
    weight: float  # 0.0 to 1.0
    max_tokens: int
    prompt: str
    requires_structured_output: bool = False  # True for FSRs, SMs
    output_format: str = "text"  # "text" or "json"

class FSCContentTemplate:
    """
    Complete FSC content generation template.
    Each section has weight (importance) and specific prompt for LLM.
    """
    
    def __init__(self):
        self.sections = {
            "introduction": SectionTemplate(
                weight=0.10,
                max_tokens=400,
                prompt="""Generate a professional introduction for the Functional Safety Concept.

**System:** {item_name}
**Description:** {item_context}

The introduction should:
- Describe the item/system briefly
- State the purpose of this FSC per ISO 26262-3:2018, Clause 7
- Reference relevant HARA outputs
- Be professional and concise

Generate ONLY the introduction text.""",
                output_format="text"
            ),
            
            "safety_goal_summary": SectionTemplate(
                weight=0.12,
                max_tokens=500,
                prompt="""Summarize the safety goals from HARA for FSC context.

**Safety Goals:**
{safety_goals_list}

Provide an overview that:
- Lists all safety goals
- Groups by ASIL level if helpful
- Explains the overall safety approach
- References ISO 26262-3:2018, Clause 6

Generate a clear summary.""",
                output_format="text"
            ),
            
            "functional_safety_requirements": SectionTemplate(
                weight=0.35,
                max_tokens=1400,
                prompt="""Based on the safety strategies, derive Functional Safety Requirements (FSRs).

**Safety Goal:** {safety_goal}
**ASIL:** {asil}
**Strategies:**
{strategies}

Generate 5-8 FSRs in JSON format:
[
  {{
    "id": "FSR-{goal_id}-TYPE-001",
    "description": "Clear, testable requirement",
    "type": "detection|control|mitigation|warning|transition|tolerance|degradation|timing|arbitration",
    "asil": "{asil}",
    "safe_state": "Description of safe state",
    "ftti": "Xms or TBD",
    "validation_criteria": ["criterion 1", "criterion 2"],
    "verification_method": "Analysis|Inspection|Testing|Walkthrough"
  }}
]

Return ONLY valid JSON array.""",
                requires_structured_output=True,
                output_format="json"
            ),
            
            "safety_mechanisms": SectionTemplate(
                weight=0.25,
                max_tokens=1000,
                prompt="""Identify safety mechanisms to implement the FSRs.

**FSRs to cover:**
{fsr_list}

For each FSR, identify appropriate mechanisms. Generate 3-6 total.

Return JSON array:
[
  {{
    "id": "SM-{goal_id}-001",
    "name": "Mechanism name",
    "description": "Clear description",
    "type": "detection|mitigation|control",
    "fsr_coverage": ["FSR-XXX-001", "FSR-XXX-002"],
    "asil": "{asil}",
    "implementation": "Hardware|Software|Combined"
  }}
]

Return ONLY valid JSON array.""",
                requires_structured_output=True,
                output_format="json"
            ),
            
            "architectural_allocation": SectionTemplate(
                weight=0.10,
                max_tokens=400,
                prompt="""Describe the architectural allocation strategy for FSRs.

**FSRs:** {num_fsrs} total
**Architecture:** {architecture_description}

Explain:
- How FSRs are allocated to components
- Freedom from interference considerations
- ASIL decomposition approach (if any)
- Interface requirements

Generate allocation strategy description.""",
                output_format="text"
            ),
            
            "verification_strategy": SectionTemplate(
                weight=0.08,
                max_tokens=320,
                prompt="""Define verification strategy for FSC per ISO 26262-3:2018, Clause 7.4.4.

**FSRs:** {num_fsrs} requirements
**ASIL Levels:** {asil_levels}

Define:
- Verification methods (analysis, inspection, testing, walkthrough)
- Acceptance criteria
- Verification stages
- Responsible parties

Be specific per ISO 26262-8:2018, Table 5.""",
                output_format="text"
            )
        }
    
    def get_section_template(self, section_name: str) -> SectionTemplate:
        """Get template for a specific section"""
        if section_name not in self.sections:
            raise ValueError(f"Unknown section: {section_name}")
        return self.sections[section_name]
    
    def get_prompt(self, section_name: str, context: Dict[str, Any]) -> str:
        """Get formatted prompt for a section with context"""
        template = self.get_section_template(section_name)
        return template.prompt.format(**context)
    
    def get_section_order(self) -> List[str]:
        """Get sections in order of generation"""
        return list(self.sections.keys())