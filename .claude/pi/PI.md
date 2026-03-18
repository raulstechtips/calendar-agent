---
name: PI-1
theme: "MVP — AI Calendar Assistant"
started: 2026-03-14
target: 2026-03-17
status: active
---

# PI-1: MVP — AI Calendar Assistant

## Goals
Ship a functional AI calendar assistant: Google OAuth, chat with LangGraph agent, calendar CRUD with human-in-the-loop confirmation, deployed to Azure Container Apps.

## Epics

### Epic: Auth & Google OAuth (#2)
**Features:**
- [x] Google OAuth with refresh tokens (stories: #8, #9, #10, #11, #13, #59, #67)

### Epic: FastAPI Backend Core (#3)
**Features:**
- [x] Backend scaffold + middleware (stories: #12, #14, #31)

### Epic: LangGraph Agent Pipeline (#4)
**Features:**
- [x] Agent setup + calendar tools (stories: #16, #17, #18, #19)

### Epic: Azure AI Search Integration (#5)
**Features:**
- [x] Search index + embedding pipeline (stories: #20, #21, #22)

### Epic: Frontend Chat & Calendar UI (#6)
**Features:**
- [x] Chat UI + calendar view (stories: #23, #24)

### Epic: Infrastructure & Deployment (#7)
**Features:**
- [x] Terraform modules + Container Apps (stories: #47, #48, #49, #50, #51, #64, #71)

## Dependency Graph
- Backend scaffold (#12) → blocks Redis (#14), agent setup (#16), user endpoints (#13), token storage (#10)
- Google OAuth (#9) → blocks auth proxy (#11), backend verification (#59)
- Backend verification (#59) → blocks calendar tools (#17), ingestion (#15)
- Search index (#20) → blocks embedding pipeline (#21) → blocks search tool (#22)
- Prompt defense (#18) → must precede content safety (#19)
- All code stories → block Dockerfiles (#26) → blocks Container Apps (#50)

## Worktree Strategy
- Worktree A (Frontend): #8 → #9 → #11 → #23, #24
- Worktree B (Backend): #12 → #14, #13 → #10 → #59
- Worktree C (Agent): #16 → #17, #18 → #19, #22
- Worktree D (Infra): #47 → #48, #64, #71 → #49 → #50 → #51
