"""CLI adapter — thin client that talks to the Autonomous Factory backend API."""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://localhost:8000"


def _api(method: str, path: str, data: dict | None = None, base: str = DEFAULT_BASE) -> dict:
    url = f"{base}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read()) if e.readable() else {"detail": str(e)}
        print(f"Error {e.code}: {err.get('detail', err)}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print(f"Is the server running at {base}?", file=sys.stderr)
        sys.exit(1)


def cmd_health(args):
    data = _api("GET", "/health", base=args.base)
    print(f"Status: {data['status']}  Version: {data['version']}")


def cmd_create(args):
    payload = {"title": args.title, "raw_prompt": args.prompt}
    if args.workspace:
        payload["workspace_id"] = args.workspace
    data = _api("POST", "/api/missions", payload, base=args.base)
    print(f"Created mission {data['id']}")
    print(f"  Title:  {data['title']}")
    print(f"  Status: {data['status']}")
    if data.get("contract"):
        print(f"  Objective: {data['contract']['normalized_objective']}")
    if data.get("findings"):
        for f in data["findings"]:
            print(f"  [{f['severity']}] {f['message']}")


def cmd_list(args):
    params = f"?limit={args.limit}"
    if args.status:
        params += f"&status={args.status}"
    data = _api("GET", f"/api/missions{params}", base=args.base)
    print(f"Missions ({data['total']} total):\n")
    for m in data["missions"]:
        print(f"  {m['id'][:8]}  [{m['status']:>10}]  {m['title']}")


def cmd_get(args):
    data = _api("GET", f"/api/missions/{args.id}", base=args.base)
    print(json.dumps(data, indent=2))


def cmd_start(args):
    data = _api("POST", f"/api/missions/{args.id}/start", base=args.base)
    print(f"Mission {data['id'][:8]} -> {data['status']}")
    wi = _api("GET", f"/api/missions/{args.id}/work-items", base=args.base)
    for item in wi:
        print(f"  [{item['role']:>12}] {item['title']} ({item['status']})")


def cmd_advance(args):
    data = _api("POST", f"/api/missions/{args.id}/advance", base=args.base)
    print(f"Mission {data['id'][:8]} -> {data['status']}")


def cmd_cancel(args):
    data = _api("POST", f"/api/missions/{args.id}/cancel", base=args.base)
    print(f"Mission {data['id'][:8]} -> {data['status']}")


def cmd_events(args):
    data = _api("GET", f"/api/missions/{args.id}/events?limit={args.limit}", base=args.base)
    for ev in data:
        print(
            f"  {ev['created_at']}  [{ev['severity']}] {ev['event_type']}"
            f"  {json.dumps(ev.get('payload') or {})}"
        )


def cmd_approvals(args):
    data = _api("GET", "/api/approvals", base=args.base)
    if not data:
        print("No pending approvals.")
        return
    for a in data:
        print(f"  {a['id'][:8]}  mission={a['mission_id'][:8]}  {a['reason']}")


def cmd_approve(args):
    payload = {"status": "approved", "decided_by": args.actor or "cli-operator"}
    data = _api("POST", f"/api/approvals/{args.id}/decide", payload, base=args.base)
    print(f"Approval {data['id'][:8]} -> {data['status']}")


def cmd_reject(args):
    payload = {"status": "rejected", "decided_by": args.actor or "cli-operator"}
    data = _api("POST", f"/api/approvals/{args.id}/decide", payload, base=args.base)
    print(f"Approval {data['id'][:8]} -> {data['status']}")


def main():
    parser = argparse.ArgumentParser(prog="af", description="Autonomous Factory CLI")
    parser.add_argument("--base", default=DEFAULT_BASE, help="Backend API base URL")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("health", help="Check server health")

    p_create = sub.add_parser("create", help="Create a new mission")
    p_create.add_argument("title", help="Mission title")
    p_create.add_argument("prompt", help="Mission prompt text")
    p_create.add_argument("--workspace", help="Workspace ID")

    p_list = sub.add_parser("list", help="List missions")
    p_list.add_argument("--status", help="Filter by status")
    p_list.add_argument("--limit", type=int, default=20)

    p_get = sub.add_parser("get", help="Get mission details")
    p_get.add_argument("id", help="Mission ID")

    p_start = sub.add_parser("start", help="Start a compiled mission")
    p_start.add_argument("id", help="Mission ID")

    p_advance = sub.add_parser("advance", help="Advance a mission")
    p_advance.add_argument("id", help="Mission ID")

    p_cancel = sub.add_parser("cancel", help="Cancel a mission")
    p_cancel.add_argument("id", help="Mission ID")

    p_events = sub.add_parser("events", help="Show mission events")
    p_events.add_argument("id", help="Mission ID")
    p_events.add_argument("--limit", type=int, default=50)

    sub.add_parser("approvals", help="List pending approvals")

    p_approve = sub.add_parser("approve", help="Approve a request")
    p_approve.add_argument("id", help="Approval ID")
    p_approve.add_argument("--actor", help="Actor name")

    p_reject = sub.add_parser("reject", help="Reject a request")
    p_reject.add_argument("id", help="Approval ID")
    p_reject.add_argument("--actor", help="Actor name")

    args = parser.parse_args()

    commands = {
        "health": cmd_health,
        "create": cmd_create,
        "list": cmd_list,
        "get": cmd_get,
        "start": cmd_start,
        "advance": cmd_advance,
        "cancel": cmd_cancel,
        "events": cmd_events,
        "approvals": cmd_approvals,
        "approve": cmd_approve,
        "reject": cmd_reject,
    }

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands[args.command](args)


if __name__ == "__main__":
    main()
