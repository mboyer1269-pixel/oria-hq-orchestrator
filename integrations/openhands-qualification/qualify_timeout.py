"""Exercise launcher cleanup only; no SDK, network, credentials or model."""
import signal
import time

# Deliberately resist graceful termination so the launcher must clean up.
signal.signal(signal.SIGTERM, signal.SIG_IGN)
print("QUALIFICATION_TIMEOUT_PROBE_STARTED", flush=True)
time.sleep(120)
raise RuntimeError("Launcher failed to enforce its deadline")
