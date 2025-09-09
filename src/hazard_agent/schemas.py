from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict


class IdentifiedHazard(BaseModel):
    """A hazard identified from input data."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique hazard identifier (UUID or index key)")
    type: str = Field(..., description="Hazard category e.g., 'ppe_violation', 'floor_safety', 'electrical'")
    description: str = Field(..., description="Human-readable description of the hazard")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level: 'low' | 'medium' | 'high'")
    location: str = Field(..., description="Location of the hazard, e.g., 'aisle', 'warehouse floor'")
    recommendations: str = Field(..., description="Suggested action to mitigate the hazard")


class HazardIdentificationOutput(BaseModel):
    """Output of the Hazard Identification Agent."""
    model_config = ConfigDict(extra="forbid")

    hazards_detected: bool = Field(..., description="Whether hazards were detected in the input")
    hazard_count: int = Field(..., description="Number of hazards detected")
    hazards: List[IdentifiedHazard] = Field(..., description="List of identified hazards")


class PrioritizedHazard(BaseModel):
    """A hazard with assigned priority after identification."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique hazard identifier (UUID or index key)")
    type: str = Field(..., description="Hazard category e.g., 'ppe_violation', 'floor_safety'")
    description: str = Field(..., description="Human-readable description of the hazard")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level: 'low' | 'medium' | 'high'")
    priority: Literal["low", "medium", "high", "critical"] = Field(..., description="Assigned priority: 'low' | 'medium' | 'high' | 'critical'")
    rationale: str = Field(..., description="Reasoning behind the assigned priority")
    recommended_timeline: str = Field(..., description="Suggested timeline for remediation, e.g., 'immediate', '24h', '1 week'")


class HazardPrioritizationOutput(BaseModel):
    """Output of the Hazard Prioritization Agent."""
    model_config = ConfigDict(extra="forbid")

    prioritized_hazards: List[PrioritizedHazard] = Field(
        ..., description="List of hazards with assigned priority levels"
    )

class HazardOrchestratorOutput(BaseModel):
    """Combined output of the Hazard Orchestrator Agent."""
    model_config = ConfigDict(extra="forbid")

    workflow_complete: bool = Field(..., description="Whether the hazard identification and prioritization workflow is complete")
    identified_hazards: HazardIdentificationOutput = Field(..., description="Output from the Hazard Identification Agent")
    prioritized_hazards: List[PrioritizedHazard] = Field(..., description="List of hazards with assigned priority levels from the Prioritization Agent")