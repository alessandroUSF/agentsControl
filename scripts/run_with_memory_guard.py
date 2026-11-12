"""Run a local-model session of protocol v2.3 with a memory guard.

Starts the answering runner src/run_models.py ('run') or the judging runner src/run_judges_v23.py ('judge') as a
child process, with the arguments given, and checks memory every 15 s. Both runners resume where they stopped.
- Ollama's llama-server grows in memory over a long run (about 2.5 GB per 10 minutes on
  07/11). When its committed memory passes SERVER_MAX_GB, the guard asks Ollama to unload
  the model; Ollama reloads it on the next request, which frees the leaked memory.
- If free RAM < 2.5 GB or free commit < 2.0 GB on two checks in a row, it stops the run
  and unloads every Ollama model, so the computer stays usable. Re-running the same command resumes.
Every unload is also written to results/logs/manifest_<run>.jsonl (event "guard_unload"), so a reload
during a run is part of the run's provenance (round-3 audit B3-m11). Processes counted: llama-server.exe
and ollama.exe (runner and server; an upper bound).
Exit codes: 0 finished, 4 paused for low memory; any other code is the runner's own (2 not started, 3 a model
was stopped, 1 or a message: the runner refused or failed).
Examples:
  python -I scripts/run_with_memory_guard.py run --run b2_local --block 2 --models <local keys>
  python -I scripts/run_with_memory_guard.py judge --run b3_local --block 3 --answer-runs b2_local --judges <keys>
"""
import ctypes
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.request

import pathlib

PROJECT = str(pathlib.Path(__file__).resolve().parents[1])
USAGE = ("usage: python -I scripts/run_with_memory_guard.py run --run NAME [src/run_models.py arguments]\n"
         "       python -I scripts/run_with_memory_guard.py judge --run NAME [src/run_judges_v23.py arguments]")
PAUSED = 4
mode, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
if mode == "judge":
    if "--run" not in rest or rest.index("--run") + 1 >= len(rest):
        sys.exit(USAGE)
    CMD = [sys.executable, "-I", "-u", "src/run_judges_v23.py"] + rest
    LOG = PROJECT + r"\results\logs\guard_judge.log"
elif mode == "run" and "--run" in rest and rest.index("--run") + 1 < len(rest):
    run_name = rest[rest.index("--run") + 1]
    if run_name in ("full", "pilot_local", "v22_local"):
        sys.exit(f"run '{run_name}' is sealed (docs/SEALED_HASHES.md); choose another run name.")
    CMD = [sys.executable, "-I", "-u", "src/run_models.py"] + rest
    LOG = PROJECT + rf"\results\logs\guard_{run_name}.log"
else:
    sys.exit(USAGE)
if mode == "run":
    MANIFEST = pathlib.Path(PROJECT) / "results" / "logs" / f"manifest_{run_name}.jsonl"
else:   # judge mode: guard events go to the judge manifest of that run (B4 residual of m12)
    judge_run = rest[rest.index("--run") + 1] if "--run" in rest and rest.index("--run") + 1 < len(rest) else "judge"
    MANIFEST = pathlib.Path(PROJECT) / "results" / "logs" / f"manifest_judge_{judge_run}.jsonl"
RAM_MIN_GB, COMMIT_MIN_GB, EVERY_S, STATUS_EVERY_S = 2.5, 2.0, 15, 300
SERVER_MAX_GB, RECYCLE_GAP_S = 9.0, 120


class MEMSTAT(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong),
                ("total", ctypes.c_ulonglong), ("avail", ctypes.c_ulonglong),
                ("total_commit", ctypes.c_ulonglong), ("avail_commit", ctypes.c_ulonglong),
                ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ave", ctypes.c_ulonglong)]


def mem():
    m = MEMSTAT()
    m.len = ctypes.sizeof(MEMSTAT)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30, m.avail_commit / 2**30


class PMC(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + \
               [(n, ctypes.c_size_t) for n in ("pws", "ws", "a", "b", "c", "d", "pf", "ppf", "private")]


def server_private_gb():
    """Committed memory of Ollama's llama-server processes, in GB."""
    k, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
    arr, needed = (ctypes.c_ulong * 8192)(), ctypes.c_ulong()
    psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(needed))
    total = 0
    for pid in arr[:needed.value // 4]:
        h = k.OpenProcess(0x1000 | 0x0010, False, pid)
        if not h:
            continue
        buf, size = ctypes.create_unicode_buffer(512), ctypes.c_ulong(512)
        if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) and \
                buf.value.lower().endswith(("llama-server.exe", "ollama.exe")):
            pmc = PMC()
            pmc.cb = ctypes.sizeof(PMC)
            if psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
                total += pmc.private
        k.CloseHandle(h)
    return total / 2**30


def say(msg, log):
    line = f"[guard {dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    log.write(line + "\n")
    log.flush()


def unload_models(log, reason="end"):
    try:
        with urllib.request.urlopen("http://localhost:11434/api/ps", timeout=10) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
        if MANIFEST is not None and names:
            with open(MANIFEST, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"event": "guard_unload", "reason": reason, "models": names,
                                    "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}) + "\n")
        for n in names:
            body = json.dumps({"model": n, "keep_alive": 0}).encode()
            req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        say(f"unloaded from Ollama: {names or 'nothing loaded'}", log)
    except Exception as e:
        say(f"could not unload Ollama models: {e}", log)


def main():
    with open(LOG, "a", encoding="utf-8") as log:
        ram, com = mem()
        say(f"START  free RAM {ram:.1f} GB, free commit {com:.1f} GB", log)
        if ram < RAM_MIN_GB or com < COMMIT_MIN_GB:
            say("PAUSED before start: memory already too low", log)
            return PAUSED
        proc = subprocess.Popen(CMD, cwd=PROJECT, stdout=log, stderr=subprocess.STDOUT)
        low, last_status, last_recycle = 0, time.time(), 0.0
        while proc.poll() is None:
            time.sleep(EVERY_S)
            srv = server_private_gb()
            if srv > SERVER_MAX_GB and time.time() - last_recycle > RECYCLE_GAP_S:
                say(f"recycle: llama-server at {srv:.1f} GB, asking Ollama to reload the model", log)
                unload_models(log, reason="recycle")
                last_recycle = time.time()
            ram, com = mem()
            low = low + 1 if (ram < RAM_MIN_GB or com < COMMIT_MIN_GB) else 0
            if low >= 2:
                proc.terminate()
                try:
                    proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=60)
                say(f"PAUSED low memory: free RAM {ram:.1f} GB, free commit {com:.1f} GB", log)
                unload_models(log, reason="low_memory")
                return PAUSED
            if time.time() - last_status >= STATUS_EVERY_S:
                say(f"status  free RAM {ram:.1f} GB, free commit {com:.1f} GB, llama-server {srv:.1f} GB", log)
                last_status = time.time()
        code = proc.returncode
        say(f"{'DONE' if code == 0 else 'RUNNER FAILED'} exit code {code}", log)
        unload_models(log)
        return 0 if code == 0 else code


if __name__ == "__main__":
    sys.exit(main())
