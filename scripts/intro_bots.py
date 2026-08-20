"""Make every war-room member's default page a proper introduction: role,
what they do, and how to collaborate. Uses the app's own API to send one
kickoff message per bot; the bot answers from its actual SKILL.md / persona —
which doubles as an end-to-end smoke test (CLI spawns, skills load, cwd right).

    .venv/bin/python scripts/intro_bots.py            # all members
    .venv/bin/python scripts/intro_bots.py Triage     # just one
"""
import json
import sys
import time
import urllib.request

AGENT_PROMPT = (
    "Post your pinned introduction for this ops room (do NOT run any commands "
    "or tools — answer from your skill instructions only). 6-8 short lines, "
    "plain language:\n"
    "1) 岗位 — your role in one line\n"
    "2) 主要做什么 — the 2-3 things you actually do, naming the files you "
    "read and write\n"
    "3) 如何合作 — what to say to trigger me, what I hand off and to whom, "
    "and what I will never do\n"
    "Answer in English with the three Chinese headers above kept as section "
    "labels."
)
PERSONA_PROMPT = (
    "Post your pinned introduction for this ops room (no commands, stay in "
    "character, 5-6 short lines): 岗位 — who you are, team, that you're a "
    "simulated colleague; 主要做什么 — what you own; 如何合作 — when "
    "teammates should @ you and what you'll do when they do."
)


def api(port, method, path, body=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read() or "{}")


def find_port():
    for port in [8799] + list(range(8790, 8811)):
        try:
            if api(port, "GET", "/api/health").get("app") == "openmausbot":
                return port
        except Exception:
            continue
    sys.exit("OpenMausBot server not found — is the app running?")


def wait_idle(port, bot_id, timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        bot = next(b for b in api(port, "GET", "/api/bots")["bots"] if b["id"] == bot_id)
        if not bot.get("busy"):
            return bot
        time.sleep(3)
    return None


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    port = find_port()
    bots = api(port, "GET", "/api/bots")["bots"]
    targets = [b for b in bots
               if b["name"] != "Pixel" and not b.get("hidden")
               and (only is None or only.lower() in b["name"].lower())]
    for b in targets:
        prompt = PERSONA_PROMPT if "(simulated)" in b["name"] else AGENT_PROMPT
        print(f"→ {b['name']} ... ", end="", flush=True)
        api(port, "POST", f"/api/bots/{b['id']}/messages", {"text": prompt})
        done = wait_idle(port, b["id"])
        if done is None:
            print("TIMEOUT (still busy — check the app window)")
            continue
        texts = [m.get("text", "") for m in done.get("messages", [])
                 if m.get("role") == "bot" and m.get("kind") == "text" and m.get("text")]
        reply = texts[-1] if texts else "(no text reply — check thread)"
        print("ok")
        print("   " + reply.replace("\n", "\n   ")[:600] + "\n")


if __name__ == "__main__":
    main()
