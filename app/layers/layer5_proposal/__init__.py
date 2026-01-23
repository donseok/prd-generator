"""Layer 5: Proposal Generation - PRD to Customer Proposal."""

from .proposal_generator import ProposalGenerator
from .models import (
    ProposalDocument,
    ProposalContext,
    ProposalMetadata,
    ProjectOverview,
    ScopeOfWork,
    SolutionApproach,
    Timeline,
    TimelinePhase,
    Deliverable,
    ResourcePlan,
    TeamMember,
    Risk,
    RiskLevel,
)

__all__ = [
    "ProposalGenerator",
    "ProposalDocument",
    "ProposalContext",
    "ProposalMetadata",
    "ProjectOverview",
    "ScopeOfWork",
    "SolutionApproach",
    "Timeline",
    "TimelinePhase",
    "Deliverable",
    "ResourcePlan",
    "TeamMember",
    "Risk",
    "RiskLevel",
]
