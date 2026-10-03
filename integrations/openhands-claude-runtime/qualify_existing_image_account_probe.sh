#!/bin/sh
set -u
echo "== claude-agent-acp --cli --version =="
claude-agent-acp --cli --version 2>&1

echo
echo "== claude-agent-acp --cli auth status --json (field names/types/lengths only, never values) =="
AUTH_JSON="$(claude-agent-acp --cli auth status --json 2>/tmp2/auth_stderr.txt)"
AUTH_EXIT=$?
echo "exit code: $AUTH_EXIT"
if [ -s /tmp2/auth_stderr.txt ]; then
  echo "stderr (full - this is CLI guidance text: a missing-file notice and a"
  echo "suggested restore command, never a token or credential value):"
  cat /tmp2/auth_stderr.txt
fi
printf '%s' "$AUTH_JSON" | node -e '
let d="";
process.stdin.on("data",c=>d+=c);
process.stdin.on("end",()=>{
  try{
    const j=JSON.parse(d);
    if (j===null || typeof j!=="object" || Array.isArray(j)) { console.log("auth status output: JSON but not an object"); return; }
    // Same whitelist already established and reviewed elsewhere in this
    // codebase (local-runtime-probe.ts CLAUDE_AUTH_EVIDENCE_FIELDS) - these
    // four VALUES are not secrets and are already treated as safe,
    // citeable evidence. Everything else stays type/length-only.
    const VALUE_WHITELIST = ["loggedIn", "authMethod", "apiProvider", "subscriptionType"];
    for (const k of Object.keys(j)) {
      const v=j[k];
      const t = v===null ? "null" : typeof v;
      if (VALUE_WHITELIST.includes(k)) {
        console.log("  field "+k+" = "+JSON.stringify(v));
      } else {
        const len = (typeof v==="string") ? (" length="+v.length) : "";
        console.log("  field "+k+": type="+t+len);
      }
    }
  } catch(e) { console.log("auth status output: not valid JSON ("+d.length+" chars)"); }
});
'

echo
echo "== codex: no login/doctor/auth subcommand exists in this image's codex-acp binary =="
echo "confirmed via --help (only -c/--config and -h/--help; no subcommands; no bare"
echo "'codex' binary on PATH here) - not attempted, nothing to redact."
