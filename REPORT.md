# Worker1 desktop diagnosis — 2026-10-22

## Verified blocker

Read-only authenticated checks at 16:16 UTC establish a dead runtime, not a wrong display number or just a stale client URL:

- Worker UI http://100.108.186.69:50080/ returns authenticated200. Browser navigation reaches the expected login page, but interactive authenticated browser verification is blocked: browser_vault list has no matching Agent Zero login. The existing approved server-side Bitwarden helper successfully authenticates the API without extracting browser credentials.
- Stored dedicated desktop is display120, backend TCP14500. Manifest Xvfb584, XFCE606, Xpra1166 are all nonexistent; loopback14500 refuses connection. Process listing contains no desktop processes. Both :120 and :0 fail xdpyinfo. X120 and X0 filesystem sockets are stale, not proof of a running display.
- Supported read-only desktop state reports ok=false, zero geometry/windows, Cannot open display :120.
- Correct stable, non-secret desktop route is http://100.108.186.69:50080/desktop/session/agent-zero-desktop/ . It is NOT currently usable: authenticated307 to index.html with only a path query, followed by404. No working iframe or live takeover has been verified.
- All six context records are idle/unpaused. No input was sent and no documents opened. Both container IDs/start times match integration evidence; neither container was bounced.

## Proposed repair, NOT executed

Parent was notified before any runtime operation. Request parent go-ahead for existing worker1 native Desktop activation, not container recreation or model changes:

1. Recheck context activity and desktop processes to avoid racing human usage. Preserve existing profile, manifest and appdata; do not delete stale sockets or lockfiles blindly.
2. Authenticate using approved server-side vault credentials with CSRF and Origin; POST `/api/plugins/_desktop/desktop_session` JSON `{"action":"desktop"}`. Installed code ensures the existing system desktop, rejects dead manifest PIDs, and spawns Xvfb/XFCE/Xpra if absent. It uses the existing profile and stable system session; no new feature/container is necessary. It can also terminate/reap owned dead runtime processes, so execution was withheld under the parent's notice gate. Do not log returned token fields/full payload.
3. Read back action=state with include_screenshot=false; independently verify live Xvfb/XFCE/Xpra, accepting backend port, nonzero geometry and unchanged context metadata/container identity. If native activation fails because of stale X lock/socket, inspect lock owner/process/socket before proposing exact targeted cleanup; no blind deletion.
4. Supply a matching worker1 login through supported browser vault. Current browser vault cannot access the remote Mac Bitwarden item automatically. Use the documented interactive `HERMES_HOME=/home/helix/.hermes-minimal hermes vault add --kind login` as helix with origin http://100.108.186.69:50080, then list/fill via browser_vault; never inject cookies or type passwords through browser tools.
5. Use the existing authenticated worker Desktop control/returned session URL. Require actual connected Xpra, then perform pointer/keyboard checks only in a new benign test window after ensuring no human use; leave user documents untouched. A200 HTML frame alone is not acceptance.

No service/container restart, application/model edit, credential export, context mutation, or Creator Studio change was performed. No live desktop usability claim is warranted.

## Files

`readonly-evidence.json` holds sanitized authenticated API, PID, endpoint and identity evidence. `probe.py` is a read-only probe importing the existing approved credential helper (not a production secret resolver). Copied installed nonsecret source in this directory documents the exact native API, session-manager and URL semantics. These are investigation copies, not deployed patches.
