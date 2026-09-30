"""Apply the reviewed bridge-factory extension to an isolated SDK installation."""
import hashlib
import importlib.metadata
import json
from pathlib import Path

VERSION = "1.50.0"
SOURCE_SHA256 = "8c949ea7053c74ef42d5ee1f775069cbefe7fe4f59d922ccf724595717f541f9"
ANCHOR = '    # Override required fields with ACP-appropriate defaults\n'
FACTORY = '''    def create_acp_bridge(self) -> _OpenHandsACPBridge:
        """Create this instance's ACP client bridge.

        Downstream extension point. Upstream auto-approval remains explicit in
        the default bridge; subclasses may return a scoped permission bridge.
        Called whenever a subprocess session is initialized or restarted.
        """
        return _OpenHandsACPBridge()

'''


def main():
    distribution = importlib.metadata.distribution("openhands-sdk")
    if distribution.version != VERSION:
        raise RuntimeError("Unsupported SDK version")
    path = Path(distribution.locate_file("openhands/sdk/agent/acp_agent.py"))
    original = path.read_bytes()
    if hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("SDK source differs; refuse patch")
    source = original.decode("utf-8")
    if source.count(ANCHOR) != 1 or source.count("        client = _OpenHandsACPBridge()\n") != 1:
        raise RuntimeError("SDK patch anchors differ")
    patched = source.replace(ANCHOR, FACTORY + ANCHOR).replace(
        "        client = _OpenHandsACPBridge()\n", "        client = self.create_acp_bridge()\n")
    compile(patched, str(path), "exec")
    path.write_bytes(patched.encode("utf-8"))
    print(json.dumps({"sdkVersion": VERSION, "originalSha256": SOURCE_SHA256,
                      "patchedSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "extension": "ACPAgent.create_acp_bridge", "productionQualified": False}))


if __name__ == "__main__":
    main()
