"""Second, bounded patch: only the already-qualified permission factory source."""
import hashlib
import importlib.metadata
from pathlib import Path
import json

EXPECTED = "7a496b59265b8139e3dd965e9ef95e28133db5cfa4b48ee20da12c328e152455"
FACTORY = '''    def build_acp_session_meta(self, agent_name: str) -> dict[str, Any]:
        """Instance-scoped metadata for new_session; downstream extension only."""
        return build_session_model_meta(agent_name, self.acp_model)

'''


def main():
    dist=importlib.metadata.distribution("openhands-sdk")
    if dist.version != "1.50.0":
        raise RuntimeError("Unsupported SDK version")
    path=Path(dist.locate_file("openhands/sdk/agent/acp_agent.py"))
    original=path.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED:
        raise RuntimeError("Expected qualified permissions source")
    source=original.decode()
    anchor="    def create_acp_bridge(self) -> _OpenHandsACPBridge:\n"
    call="                session_meta = build_session_model_meta(agent_name, self.acp_model)\n"
    if source.count(anchor) != 1 or source.count(call) != 1:
        raise RuntimeError("SDK budget patch anchors differ")
    patched=source.replace(anchor,FACTORY+anchor).replace(call,"                session_meta = self.build_acp_session_meta(agent_name)\n")
    compile(patched,str(path),"exec")
    path.write_bytes(patched.encode())
    print(json.dumps({"originalSha256":EXPECTED,"patchedSha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "extension":"ACPAgent.build_acp_session_meta","productionQualified":False}))


if __name__=="__main__": main()
