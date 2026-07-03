#!/usr/bin/env python3
"""
evidence_runner.py - Run ONE command, capture everything for the report.

AUTHORIZED PENETRATION TESTING USE ONLY.

Purpose: during initial access you want each command executed individually so
the request AND response are captured cleanly per-step. This wraps a single
command, streams its output live to your terminal, and simultaneously writes:
  * <label>.<timestamp>.log   - full combined stdout/stderr transcript
  * <label>.<timestamp>.json  - metadata: exact argv, start/end time,
                                duration, exit code, operator, host

Usage:
  python3 evidence_runner.py --label responder_analyze -- responder -I eth0 -A
  python3 evidence_runner.py --label relay_targets -- \
      nxc smb 10.10.10.0/24 --gen-relay-list targets.txt
  python3 evidence_runner.py --label ntlmrelay -- \
      ntlmrelayx.py -tf targets.txt -smb2support -i

Everything after `--` is run verbatim. Nothing is interpreted or modified.
"""

import argparse
import datetime
import json
import os
import socket
import subprocess
import sys


def ts_file():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def ts_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def main():
    ap = argparse.ArgumentParser(
        description="Run a single command and capture it as reporting evidence.")
    ap.add_argument("--label", required=True,
                    help="Short step label, e.g. 'responder_analyze'.")
    ap.add_argument("--outdir", default="evidence",
                    help="Directory for evidence artifacts (default: evidence/).")
    ap.add_argument("--operator", default=os.environ.get("USER", "unknown"),
                    help="Operator name for the evidence record.")
    ap.add_argument("command", nargs=argparse.REMAINDER,
                    help="The command to run, after `--`.")
    args = ap.parse_args()

    cmd = args.command
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        ap.error("No command supplied. Put it after `--`.")

    os.makedirs(args.outdir, exist_ok=True)
    stamp = ts_file()
    base = os.path.join(args.outdir, f"{args.label}.{stamp}")
    log_path = base + ".log"
    meta_path = base + ".json"

    header = (
        f"# label     : {args.label}\n"
        f"# operator  : {args.operator}\n"
        f"# host      : {socket.gethostname()}\n"
        f"# command   : {' '.join(cmd)}\n"
        f"# started   : {ts_iso()}\n"
        f"{'-' * 60}\n"
    )
    print(header, end="")

    start = datetime.datetime.now()
    transcript = []
    rc = None
    try:
        with open(log_path, "w", encoding="utf-8") as logf:
            logf.write(header)
            logf.flush()
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1)
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                logf.write(line)
                logf.flush()
                transcript.append(line)
            proc.wait()
            rc = proc.returncode
    except FileNotFoundError:
        print(f"\n[!] Command not found: {cmd[0]}", file=sys.stderr)
        rc = 127
    except KeyboardInterrupt:
        # Responder / ntlmrelayx are long-running; Ctrl-C is the normal stop.
        print("\n[*] Interrupted by operator (expected for listeners).")
        rc = 130

    end = datetime.datetime.now()
    meta = {
        "label": args.label,
        "operator": args.operator,
        "host": socket.gethostname(),
        "command": cmd,
        "command_string": " ".join(cmd),
        "started": start.isoformat(timespec="seconds"),
        "ended": end.isoformat(timespec="seconds"),
        "duration_seconds": round((end - start).total_seconds(), 2),
        "exit_code": rc,
        "log_file": log_path,
        "line_count": len(transcript),
    }
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2)

    print(f"\n{'-' * 60}")
    print(f"[*] Exit code : {rc}")
    print(f"[*] Duration  : {meta['duration_seconds']}s")
    print(f"[*] Transcript: {log_path}")
    print(f"[*] Metadata  : {meta_path}")


if __name__ == "__main__":
    main()
