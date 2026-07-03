# evidence_runner
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
