"""Qualify real SDK arun/interrupt -> ACP cancel against a synthetic peer only."""
import asyncio
import importlib.metadata
import json
from pathlib import Path
import signal
import sys
import tempfile

from openhands.sdk import Conversation
from openhands.sdk.agent import ACPAgent


def deadline(signum, frame):
    raise TimeoutError("Cancellation qualification exceeded 40 seconds")


async def main():
    assert importlib.metadata.version("openhands-sdk") == "1.50.0"
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(40)
    with tempfile.TemporaryDirectory(prefix="hq-acp-cancel-") as directory:
        root = Path(directory)
        receipt = root / "cancel-receipt.json"
        events = []

        def observe(event):
            payload = event.model_dump(mode="json")
            events.append(payload)

        agent = ACPAgent(
            acp_command=[sys.executable, str(Path(__file__).with_name("fake_acp.py")),
                         "--cancel-probe", str(receipt)],
            acp_startup_timeout=8,
            acp_prompt_timeout=20,
        )
        conversation = Conversation(agent=agent, workspace=directory, callbacks=[observe],
                                    persistence_dir=str(root / "conversations"))
        task = None
        try:
            conversation.send_message("Wait for the synthetic cancellation probe.")
            task = asyncio.create_task(conversation.arun())
            async def wait_for_peer():
                ready = Path(str(receipt) + ".ready")
                while not ready.exists():
                    if task.done():
                        await task
                        raise AssertionError("Run finished before peer reached active prompt")
                    await asyncio.sleep(0.05)
                assert ready.read_text(encoding="utf-8") == "prompt-active"

            await asyncio.wait_for(wait_for_peer(), timeout=12)
            # Private process read is diagnostic only, pinned to the qualified SDK.
            process = agent._process
            assert process is not None and process.returncode is None
            conversation.interrupt()
            await asyncio.wait_for(asyncio.shield(task), timeout=12)
            actual = json.loads(receipt.read_text(encoding="utf-8"))
            assert actual == {"method": "session/cancel", "sessionId": "hq-synthetic-session",
                              "promptResponse": "cancelled"}, actual
            status = str(conversation.state.execution_status.value).lower()
            assert status == "paused", status
            assert task.done(), "Run task is still active"
            conversation.close()
            assert process.returncode is not None, "Synthetic peer remained alive after close"
            print(json.dumps({"sdkVersion": "1.50.0", "syntheticPeer": True,
                              "wireCancelReceived": True, "cancelledPromptReplied": True,
                              "runTaskFinished": True, "conversationStatus": status,
                              "peerExitedAfterClose": True, "modelCalls": 0,
                              "providerCredentialsUsed": False,
                              "providerCancellationQualified": False,
                              "remoteResumeQualified": False}))
        finally:
            if task is not None and not task.done():
                conversation.interrupt()
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=5)
                except (asyncio.CancelledError, TimeoutError):
                    pass
            conversation.close()
            signal.alarm(0)


if __name__ == "__main__":
    asyncio.run(main())
