# Recovery

- Poll an existing outer session instead of submitting another request. Around 30 seconds without progress, report what is active and whether it can mutate state.
- Around 60 seconds without progress for an ordinary operation, consider stopping the local wait if supported. An announced long render or import can legitimately take longer; poll its original session.
- A local timeout, cancellation, or terminated stdio bridge does not prove cancellation on the editor's main thread. Do not send overlapping work to that host.
- Once the previous local invocation has ended, use a single lightweight read-only preflight to assess responsiveness. If the editor is known to be busy, allow its operation to finish first. Never flood a blocked editor with heartbeats.
- Retry a timed-out read at most once after a successful preflight, reducing its scope. After any lost write response, inspect the target state before deciding whether anything remains to apply. If the state is unverifiable, report the uncertainty and stop.
- After two failed preflights, stop work on that host. Report the operation, last confirmed state, and diagnostics. Restarting the application or addon requires user authorization.

The CLI does not retry automatically or provide transactions. It closes its child stdio server on exit; that is distinct from restarting the GUI host. Its single-call discipline is an instruction, not a cross-process lock. Do not invoke it concurrently from other agents against the same hosts.

Do not use desktop clicking merely to bypass a stalled MCP. When a capability is absent, identify the gap and use another method within the user's requested scope.
