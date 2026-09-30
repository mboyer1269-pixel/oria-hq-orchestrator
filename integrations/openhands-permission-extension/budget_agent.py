"""Claude-only candidate: configured turn/cost guards, never a hard token cap."""
from pydantic import Field
from typing import Literal
from permission_agent import PermissionAgent


class BudgetPermissionAgent(PermissionAgent):
    hq_permission_policy: Literal["deny"] = Field(default="deny", frozen=True)
    acp_session_mode: Literal["default"] = Field(default="default", frozen=True)
    hq_max_iterations: int = Field(strict=True,ge=1,le=100,frozen=True)
    hq_max_cost_cents: int = Field(strict=True,ge=1,le=10000,frozen=True)

    def build_acp_session_meta(self, agent_name):
        metadata=super().build_acp_session_meta(agent_name)
        claude=dict(metadata.get("claudeCode",{}))
        options=dict(claude.get("options",{}))
        options.update(maxTurns=self.hq_max_iterations,maxBudgetUsd=self.hq_max_cost_cents/100,
                       allowDangerouslySkipPermissions=False)
        claude["options"]=options
        metadata["claudeCode"]=claude
        return metadata
