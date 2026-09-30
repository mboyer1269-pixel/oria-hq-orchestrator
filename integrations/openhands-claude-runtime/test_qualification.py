"""Exercise protocol verdicts without credentials, network or a model."""
import contextlib
import io
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

import qualify_initialize


class QualificationTests(unittest.IsolatedAsyncioTestCase):
    async def probe(self, responses, error=None):
        process = Mock()
        process.returncode = None
        process.stdin.drain = AsyncMock()
        process.stdout.readline = AsyncMock(side_effect=[
            (json.dumps(response) + "\n").encode() for response in responses
        ] + [b""])
        process.wait = AsyncMock(return_value=0)
        output = io.StringIO()
        with patch.object(qualify_initialize.asyncio, "create_subprocess_exec",
                          AsyncMock(return_value=process)), contextlib.redirect_stdout(output):
            if error:
                with self.assertRaisesRegex(RuntimeError, error):
                    await qualify_initialize.main()
            else:
                await qualify_initialize.main()
        process.terminate.assert_called_once()
        process.wait.assert_awaited_once()
        methods = [json.loads(call.args[0])["method"]
                   for call in process.stdin.write.call_args_list]
        self.assertNotIn("session/prompt", methods)
        self.assertNotIn("authenticate", methods)
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        if error:
            self.assertFalse(any(event.get("sessionCreated") for event in events))
        return methods, events

    async def test_success_remains_unauthenticated(self):
        methods, events = await self.probe([
            {"id": 1, "result": {"protocolVersion": 1}},
            {"id": 2, "result": {"sessionId": "test-session"}},
        ])
        self.assertEqual(methods, ["initialize", "session/new"])
        self.assertTrue(events[-1]["sessionCreated"])
        self.assertFalse(events[-1]["providerAuthenticationVerified"])

    async def test_refused_session_is_failure(self):
        await self.probe([
            {"id": 1, "result": {"protocolVersion": 1}},
            {"id": 2, "error": {"code": -32000}},
        ], "Session creation rejected")

    async def test_missing_or_empty_identity_is_failure(self):
        for value in (None, "", " ", 5):
            with self.subTest(value=value):
                await self.probe([
                    {"id": 1, "result": {"protocolVersion": 1}},
                    {"id": 2, "result": {"sessionId": value}},
                ], "Missing session identity")

    async def test_initialize_refusal_never_opens_session(self):
        methods, _ = await self.probe([{"id": 1, "error": {"code": -32000}}],
                                      "Initialize rejected")
        self.assertEqual(methods, ["initialize"])

    async def test_protocol_mismatch_never_opens_session(self):
        for version in (2, True, "1", None):
            with self.subTest(version=version):
                methods, _ = await self.probe([
                    {"id": 1, "result": {"protocolVersion": version}},
                ], "Unsupported protocol")
                self.assertEqual(methods, ["initialize"])

    async def test_disconnect_during_session_is_failure(self):
        await self.probe([{"id": 1, "result": {"protocolVersion": 1}}],
                         "Adapter closed before session response")


if __name__ == "__main__":
    unittest.main()
