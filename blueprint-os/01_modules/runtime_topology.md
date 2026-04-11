# Runtime Topology Module

## Purpose
Describe the runtime shape of the standalone platform.

## Baseline topology

### Frontend
- standalone dashboard web app
- live mission list and inspector
- WebSocket or server-sent updates for runtime status

### Backend API
- mission creation/update endpoints
- approval endpoints
- reporting endpoints
- adapter-facing endpoints

### Control-plane worker
- mission compiler
- orchestrator/controller
- queue management
- evidence/failure/recovery logic

### Tool execution worker(s)
- workspace file operations
- terminal commands
- VCS/test/build integrations
- bounded external fetch/research jobs where allowed

### Persistence services
- relational database for mission/state truth
- file/object storage for artifacts, reports, and evidence
- optional cache/queue for throughput and concurrency

## Initial deployment modes
- local single-machine docker-compose or native processes
- remote development server for heavier workloads
- later multi-worker distributed topology

## Adapter topology
Adapters should be clients, not hosts:
- editor adapter calls backend
- backend owns truth and orchestration
- adapter streams visible status only
