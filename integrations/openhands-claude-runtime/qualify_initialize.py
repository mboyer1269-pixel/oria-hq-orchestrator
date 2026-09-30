"""Real Claude ACP initialization/session probe. Never prompts or authenticates."""
import asyncio
import json


async def main():
    process = await asyncio.create_subprocess_exec(
        "claude-agent-acp", stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    try:
        message = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": 1, "clientCapabilities": {},
            "clientInfo": {"name": "hq-qualification", "version": "1.0.0"}}}
        process.stdin.write((json.dumps(message) + "\n").encode())
        await process.stdin.drain()
        async def receive():
            for _ in range(20):
                line = await process.stdout.readline()
                if not line:
                    raise RuntimeError("Adapter closed before initialization")
                response = json.loads(line)
                if response.get("id") == 1:
                    if "error" in response:
                        raise RuntimeError("Initialize rejected")
                    result = response["result"]
                    if type(result.get("protocolVersion")) is not int or result["protocolVersion"] != 1:
                        raise RuntimeError("Unsupported protocol version")
                    print(json.dumps({"realClaudeAcpInitialized": True,
                        "protocolVersion": result["protocolVersion"],
                        "advertisedAuthMethods": [entry["id"] for entry in result.get("authMethods", [])],
                        "sessionCreated": False, "modelPromptSent": False}))
                    return result
            raise RuntimeError("Initialization response not received")
        await asyncio.wait_for(receive(), timeout=15)
        session = {"jsonrpc": "2.0", "id": 2, "method": "session/new",
                   "params": {"cwd": "/workspace", "mcpServers": []}}
        process.stdin.write((json.dumps(session) + "\n").encode())
        await process.stdin.drain()
        async def session_response():
            for _ in range(20):
                line = await process.stdout.readline()
                if not line:
                    raise RuntimeError("Adapter closed before session response")
                response = json.loads(line)
                if response.get("id") == 2:
                    if "error" in response:
                        print(json.dumps({"sessionCreated": False,
                                          "sessionErrorCode": response["error"].get("code"),
                                          "modelPromptSent": False}))
                        raise RuntimeError("Session creation rejected")
                    else:
                        session_id = response["result"].get("sessionId")
                        if not isinstance(session_id, str) or not session_id.strip():
                            raise RuntimeError("Missing session identity")
                        print(json.dumps({"sessionCreated": True, "modelPromptSent": False,
                                          "providerAuthenticationVerified": False}))
                    return
            raise RuntimeError("Session response not received")
        await asyncio.wait_for(session_response(), timeout=10)
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except TimeoutError:
                process.kill()
                await process.wait()


if __name__ == "__main__":
    asyncio.run(main())
