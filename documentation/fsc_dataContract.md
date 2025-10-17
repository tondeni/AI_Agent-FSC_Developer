# FSC Data Contract v1.0
**Contract between FSC Developer and Output Formatter plugins**

## Working Memory Key
`fsc_structured_content` → Dictionary with FSC data

## Schema
{
  "system_name": "string",
  "introduction": "string",
  "safety_goal_summary": "string",
  "functional_safety_requirements": [
    {
      "id": "string",
      "description": "string",
      "type": "detection|control|mitigation|warning|...",
      "asil": "A|B|C|D|QM",
      "safety_goal_id": "string",
      "safe_state": "string",
      "ftti": "string",
      "validation_criteria": ["string"],
      "verification_method": "string",
      "allocated_to": "string|null",
      "operating_modes": "string"
    }
  ],
  "safety_mechanisms": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "type": "detection|mitigation|control",
      "fsr_coverage": ["FSR-ID"],
      "asil": "string",
      "implementation": "Hardware|Software|Combined"
    }
  ],
  "architectural_allocation": "string",
  "verification_strategy": "string",
  "metadata": {
    "generation_date": "ISO datetime",
    "generator_version": "string",
    "schema_version": "1.0"
  }
}
