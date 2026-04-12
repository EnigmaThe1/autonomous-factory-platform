#!/usr/bin/env python3
import json
import sys

def main():
    data = json.load(sys.stdin)
    print("# Capability Activation Checklist")
    print()
    print("## Required now")
    for item in data.get("required_now", []):
        print(f"- [ ] Activate `{item}`")
    print()
    print("## Useful later")
    for item in data.get("useful_later", []):
        print(f"- [ ] Keep `{item}` deferred unless triggered")
    print()
    print("## Notes")
    print(f"- Mission: {data.get('mission','')}")
    print(f"- {data.get('note','')}")
if __name__ == "__main__":
    main()
