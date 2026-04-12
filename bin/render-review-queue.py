#!/usr/bin/env python3
import json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
queue = json.loads((root/'capabilities'/'review-queue.json').read_text())
print('REVIEW QUEUE')
for item in queue['items']:
    print(f"- {item['queue_id']} | {item['capability_id']} | {item['priority']} | {item['status']} | {item['reason']}")
