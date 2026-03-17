# CI/CD Pipeline — Working Document (Issue #28)

Tracking all open items, decisions, and implementation details for the GitHub Actions CI/CD pipeline.

---

## Item 1: Network Access — GitHub Actions → ACR + Container Apps

### Current State

| Resource | Public Access | IP Restrictions | Notes |
|----------|--------------|-----------------|-------|
| ACR | `public_network_access_enabled = true` | **None** (no `network_rule_set`) | Basic SKU — no PE support. Comment in TF: "Required for CI image push" |
| Container Apps Env | `internal_load_balancer_enabled = false` | N/A | Externally reachable, but irrelevant — CD deploys via Azure management plane, not ingress |
| Key Vault | Public + PE | `deployer_ip_cidrs` ACL | Behind VPN allowlist |
| AI Services | Public + PE | `deployer_ip_cidrs` ACL | Behind VPN allowlist |

### Assessment

- **ACR**: GitHub-hosted runners CAN push images — no network blocker. Public access is already enabled with no IP filter. This was intentional per the TF comment.
- **Container Apps**: Deployment uses `az containerapp update` which goes through the Azure Resource Manager (ARM) control plane, not through the app's ingress. GitHub runners can reach ARM without any VNet access. **No network blocker.**
- **Key Vault**: GitHub Actions does NOT need direct KV access. Container Apps pull secrets from KV at runtime via managed identity. **No blocker.**

### Verdict

> **Network access is not an issue for either ACR push or Container Apps deployment.** Both operations go through public Azure APIs (ACR registry endpoint, ARM control plane). The VPN ACL on KV/AI services doesn't affect CI/CD because those are runtime concerns, not deployment concerns.

### Security Note

ACR with `admin_enabled = false` means there is no username/password login. The **only** way to push or pull is via Entra ID authentication (managed identity, service principal, or `az acr login`). Public network access means the endpoint is reachable, not that it's open — unauthenticated requests get a 401.

### Status: **RESOLVED** — No Terraform changes needed. ACR is already Entra-ID-only.

---

## Item 2: CI/CD Triggers

### CI Workflow (`.github/workflows/ci.yml`) ✅

**Trigger**: All pull requests + pushes to `main`, excluding docs-only changes.

```yaml
on:
  pull_request:
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - '.github/CODEOWNERS'
      - 'LICENSE'
  push:
    branches: [main]
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - '.github/CODEOWNERS'
      - 'LICENSE'
```

**Jobs**: lint, typecheck, test (frontend + backend in parallel).

### CD Workflow (`.github/workflows/cd.yml`) ✅

**Trigger model**: Option A — `on: push` to `main` and `develop`, with GitHub Environment approval gate.

```yaml
on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**/*.md'
      - 'docs/**'
      - '.github/CODEOWNERS'
      - 'LICENSE'
```

**Approval gate**: On the **first job** (build + deploy are a single gated unit). The entire workflow pauses before any build or push happens — we don't want to build an image and then not deploy it.

```yaml
jobs:
  detect-changes:
    # Lightweight job — runs BEFORE the gate to determine what changed
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.changes.outputs.frontend }}
      backend: ${{ steps.changes.outputs.backend }}
      frontend_version: ${{ steps.versions.outputs.frontend }}
      backend_version: ${{ steps.versions.outputs.backend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            frontend: 'frontend/**'
            backend: 'backend/**'
      - id: versions
        run: |
          echo "frontend=$(jq -r .version frontend/package.json)" >> "$GITHUB_OUTPUT"
          echo "backend=$(grep '^version' backend/pyproject.toml | sed 's/.*"\(.*\)"/\1/')" >> "$GITHUB_OUTPUT"

  build-and-deploy:
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true' || needs.detect-changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    environment: production      # <-- Approval gate here: pauses BEFORE build
    steps:
      # Build + push frontend (conditional)
      # Build + push backend (conditional)
      # Deploy frontend (conditional)
      # Deploy backend (conditional)
```

#### Why This Structure

- **`detect-changes`** is ungated and fast (~10s) — determines which services changed and reads their versions
- **`build-and-deploy`** is gated by the `production` environment — nothing builds until an owner approves
- If only frontend changed, backend steps are skipped (and vice versa)
- If only `.md` files changed, the workflow doesn't trigger at all (`paths-ignore`)
- Both `main` and `develop` go through the same approval gate

#### Selective Deployment

The `detect-changes` job handles this automatically via path detection. No manual parameterization needed for the push trigger. For manual reruns or edge cases, we can add `workflow_dispatch` with service selection inputs:

```yaml
on:
  push:
    branches: [main, develop]
    paths-ignore: [...]
  workflow_dispatch:
    inputs:
      deploy_frontend:
        description: 'Deploy frontend'
        type: boolean
        default: true
      deploy_backend:
        description: 'Deploy backend'
        type: boolean
        default: true
```

This gives both automatic (push → detect changes) and manual (workflow_dispatch → pick services) deployment.

#### OIDC Federated Credentials: Branch Subjects

Since CD triggers from both `main` and `develop`, we need **two federated credentials** (or one using the `environment:production` subject instead of branch-based):

| Option | Subject Claim | Federated Credentials Needed |
|--------|--------------|------------------------------|
| **Branch-based** | `repo:org/repo:ref:refs/heads/main` + `repo:org/repo:ref:refs/heads/develop` | 2 |
| **Environment-based** | `repo:org/repo:environment:production` | 1 |

**Recommendation**: Environment-based subject. Since both branches use the `production` environment, a single federated credential with subject `repo:org/repo:environment:production` covers both. Simpler, and the approval gate is the real security boundary anyway.

### GitHub Environment Setup

The environment can be created via the GitHub API. **Manual step** (one-time, requires repo admin):

```bash
# 1. Create the environment
gh api repos/:owner/:repo/environments/production -X PUT

# 2. Add required reviewers (replace USER_ID with your GitHub user ID)
# First, get your user ID:
gh api user -q '.id'

# Then set the protection rule:
gh api repos/:owner/:repo/environments/production -X PUT \
  -f 'reviewers[][type]=User' \
  -F "reviewers[][id]=<YOUR_USER_ID>" \
  --input - <<< '{"reviewers":[{"type":"User","id":<YOUR_USER_ID>}]}'
```

Alternatively, in the GitHub UI: **Settings → Environments → New environment → "production" → Add required reviewers**.

### Status: **RESOLVED**

- [x] Trigger model: Option A (push to main/develop + environment approval gate)
- [x] CI also runs on pushes to `main`
- [x] CD branches: `main` and `develop`
- [x] Approval gate covers build + deploy (single gated job)
- [x] Selective deployment via path detection + optional workflow_dispatch inputs

---

## Item 3: Container Apps Revision Suffix + Image Tagging

### The Quirk

Container Apps requires a **unique revision suffix** for each deployment. If you deploy the same image tag twice, the revision suffix collision causes a failure. Additionally, redeploying an older version needs special handling.

### Revision Suffix Format

Container Apps revision suffix constraints:
- Lowercase alphanumeric + hyphens only
- Max 64 characters
- Must be unique per app

Format: `v{major}-{minor}-{patch}-{short-sha}`
Example: `v0-1-0-a3b4c5d`

### Image Tagging Strategy

**Always tag images with `{version}-{short-sha}`** — this makes every image tag unique per commit and eliminates most collision issues.

```
Image tag:      frontend:0.1.0-a3b4c5d    (unique per build)
Revision suffix: v0-1-0-a3b4c5d           (derived from image tag)
```

At build time, apply multiple tags in a single `docker build` / `docker push`:
- `frontend:0.1.0-a3b4c5d` — immutable deployment tag
- `frontend:0.1.0` — "latest for this version" convenience tag
- `frontend:latest` — convenience tag

### Proposed Flow

```
Normal deployment (code changed, new build):
  1. Read version from package.json / pyproject.toml → 0.1.0
  2. Get short SHA from git → a3b4c5d
  3. Build image, tag as:  acr.azurecr.io/frontend:0.1.0-a3b4c5d
  4. Also tag with:        acr.azurecr.io/frontend:0.1.0
  5. Push both tags
  6. Deploy with --image frontend:0.1.0-a3b4c5d --revision-suffix v0-1-0-a3b4c5d

Redeployment of older version (no code change, same image):
  1. Read version from package.json / pyproject.toml → 0.1.0
  2. Get short SHA of CURRENT commit → b7c8d9e (different from original build)
  3. Image frontend:0.1.0-b7c8d9e does NOT exist → need to create it
  4. Use az acr import to create a new tag from the base version:
       az acr import \
         --name <acr-name> \
         --source <acr-login-server>/frontend:0.1.0 \
         --image frontend:0.1.0-b7c8d9e
  5. Deploy with --image frontend:0.1.0-b7c8d9e --revision-suffix v0-1-0-b7c8d9e
```

### How `az acr import` Works for Retagging

`az acr import` supports same-registry operations. When source and target are the same ACR, it's a **server-side metadata operation** — it recognizes the manifest is identical and simply adds the new tag. No image data moves, no docker daemon needed.

**Syntax** (same-registry retag):
```bash
az acr import \
  --name myacr \
  --source myacr.azurecr.io/frontend:0.1.0 \
  --image frontend:0.1.0-b7c8d9e
```

**Key facts** (verified against Microsoft docs):
- Works on **Basic SKU** — import is a core data-plane API, not Premium-only
- Server-side only — no docker pull/push, runs in ~15s
- `--source` must be fully qualified (`<login-server>/<repo>:<tag>`) when no `--registry` flag is used
- `--force` flag needed if the target tag already exists (not our case — tags are unique due to SHA)
- Needs `AcrPush` role on the registry (which the GitHub Actions SP already has)

### Versioning Strategy

**Source of truth**: Each service owns its version in its existing config file.
- Frontend: `frontend/package.json` → `"version": "0.1.0"`
- Backend: `backend/pyproject.toml` → `version = "0.1.0"`

**Versioned independently** — they're separate services with separate deployment lifecycles. A backend-only change bumps backend version, frontend stays the same.

**Version bump process**: Manual for now (developer bumps version in the config file as part of the PR). We can automate later with conventional-commit tooling if needed.

### Status: **RESOLVED**

- [x] Image tags always include SHA — unique per commit, no collisions
- [x] Retagging older images via `az acr import` (server-side, Basic SKU compatible)
- [x] Version source: `package.json` / `pyproject.toml`, independent per service
- [x] Revision suffix format: `v{major}-{minor}-{patch}-{short-sha}`

---

## Item 4: GitHub Actions Authentication to Azure

### What GitHub Actions Needs

| Action | Required Role | Target Resource |
|--------|--------------|-----------------|
| Push images to ACR | `AcrPush` | Container Registry |
| Update Container App | `Contributor` or `Microsoft.App/containerApps/write` | Container Apps (or RG) |
| Read deployment status | `Reader` | Resource Group |

### Authentication Options

| Option | How It Works | Secrets to Manage | Rotation | Setup Complexity |
|--------|-------------|-------------------|----------|-----------------|
| **A: OIDC Federated Credentials** | App Registration + federated credential trusting GitHub's OIDC token. No secrets at all. | **Zero** — GitHub mints short-lived tokens per run | N/A — no secrets to rotate | Medium (one-time Entra ID setup) |
| **B: Service Principal + Client Secret** | App Registration + client secret stored in GitHub Secrets | Client ID, Client Secret, Tenant ID, Subscription ID | Secret expires (max 2 years), must rotate | Low |
| **C: Service Principal + Certificate** | App Registration + certificate | Client ID, Certificate (PFX), Tenant ID | Certificate expires | Medium |

### Decision: Option A (OIDC Federated Credentials) ✅

Selected because:

- **No secrets to store or rotate** — the GitHub OIDC token is minted per workflow run and is short-lived (~15 min)
- **Scoped trust** — federated credential locks the subject to a specific repo + branch; impersonation is impossible because only GitHub can sign the OIDC JWT, and GitHub sets the subject claim server-side based on the actual repo/branch
- **Azure officially supports this**: `azure/login@v2` action has native OIDC support

#### How It Works (No Secret Required)

1. GitHub runner requests an OIDC token from GitHub's built-in token service
2. GitHub mints a short-lived JWT signed with GitHub's private key, containing claims: repo, branch, environment
3. Runner presents this JWT to Entra ID: "I want to act as `<client_id>`"
4. Entra ID verifies the JWT signature against GitHub's published public keys, and checks the subject claim matches the federated credential
5. If valid, Entra ID issues a short-lived Azure access token
6. Runner uses that Azure token for ACR push / Container Apps update

The trust is **cryptographic**: GitHub signs, Azure verifies. The three values stored as GitHub repo secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) are just identifiers — knowing them without being able to mint a GitHub OIDC token from this repo is useless.

#### Terraform Location: Container Apps Module

The app registration, service principal, federated credentials, and role assignments will live in `infra/modules/container-apps/` alongside the ACR and Container App resources they grant access to.

#### What Needs to Exist in Azure (Terraform)

```hcl
# App Registration (the "service principal" identity)
resource "azuread_application" "github_actions" { ... }
resource "azuread_service_principal" "github_actions" { ... }

# Single federated credential using environment-based subject.
# Covers both main and develop branches because both use the
# "production" GitHub environment (which is the approval gate).
resource "azuread_application_federated_identity_credential" "github_production" {
  application_id = azuread_application.github_actions.id
  display_name   = "github-actions-production-env"
  audiences      = ["api://AzureADTokenExchange"]
  issuer         = "https://token.actions.githubusercontent.com"
  subject        = "repo:<org>/<repo>:environment:production"
}

# Role assignments
resource "azurerm_role_assignment" "github_acr_push" {
  scope                = azurerm_container_registry.this.id
  role_definition_name = "AcrPush"
  principal_id         = azuread_service_principal.github_actions.object_id
}

# Scoped to each Container App, not the resource group (least privilege)
resource "azurerm_role_assignment" "github_frontend_contributor" {
  scope                = azurerm_container_app.frontend.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}

resource "azurerm_role_assignment" "github_backend_contributor" {
  scope                = azurerm_container_app.backend.id
  role_definition_name = "Contributor"
  principal_id         = azuread_service_principal.github_actions.object_id
}
```

#### What Goes in GitHub Secrets

Only 3 values (none are actual secrets — they're IDs):
- `AZURE_CLIENT_ID` — App Registration client ID
- `AZURE_TENANT_ID` — Entra ID tenant ID
- `AZURE_SUBSCRIPTION_ID` — Azure subscription ID

### Terraform Changes Needed

Current state — what exists vs what's missing:

| Concern | Current State | Gap |
|---------|--------------|-----|
| ACR pull (runtime) | ✅ `AcrPull` for shared MI | None |
| ACR push (CI/CD) | ❌ No identity with `AcrPush` | Need SP + role |
| Container App deploy (CI/CD) | ❌ No identity with write access | Need SP + role |
| Registry block on Container App | ✅ Using shared MI + `identity` | None |
| Ingress config | ✅ Frontend external:3000, Backend internal:8000 | None |
| Managed identity name in registry | ✅ `identity = var.shared_identity_id` | None |
| GitHub OIDC trust | ❌ No app registration or federated credential | Need new TF resources |

### Decisions Made

- [x] **OIDC (Option A)** — no secrets to rotate, cryptographic trust
- [x] **Terraform-managed** — app registration + federated credential in `infra/modules/container-apps/` (requires `azuread` provider)
- [x] Scope of Contributor role: **scoped to the two Container App resources** (not RG-level) — least privilege

---

## Item 5: Terraform Changes Summary (pending decisions)

Once decisions are made above, the following TF changes are anticipated:

### Definite (regardless of auth choice)
- None — existing TF is correctly configured for runtime. CI/CD auth is additive.

### OIDC (Option A — selected)
- Add `azuread` provider to `infra/modules/container-apps/versions.tf`
- New resources in container-apps module: app registration, service principal, 1 federated credential (environment-based subject: `environment:production`)
- Role assignments: `AcrPush` on ACR, `Contributor` scoped to each Container App (2 assignments)
- New variables: `github_repo_name` (e.g., `"org/calendar-agent"`)
- New outputs: client ID, tenant ID (for GitHub secrets setup)

---

## Post-Apply Manual Setup

One-time steps after `terraform apply` creates the OIDC resources, before the first CD run.

### 1. Apply Terraform

```bash
cd infra/environments/dev
terraform apply
# Note the outputs:
terraform output github_actions_client_id
terraform output backend_url
terraform output acr_login_server
```

### 2. Create GitHub Environment

```bash
# Create the production environment
gh api repos/:owner/:repo/environments/production -X PUT

# Get your GitHub user ID
gh api user -q '.id'

# Add yourself as required reviewer (replace <USER_ID>)
gh api repos/:owner/:repo/environments/production -X PUT \
  --input - <<EOF
{"reviewers":[{"type":"User","id":<USER_ID>}]}
EOF
```

Or via UI: **Settings -> Environments -> New environment -> "production" -> Required reviewers**.

### 3. Set GitHub Secrets

```bash
gh secret set AZURE_CLIENT_ID --body "<from terraform output github_actions_client_id>"
gh secret set AZURE_TENANT_ID --body "<your-entra-id-tenant-id>"
gh secret set AZURE_SUBSCRIPTION_ID --body "<your-subscription-id>"
```

### 4. Set GitHub Variables

```bash
gh variable set ACR_LOGIN_SERVER --body "<from terraform output acr_login_server>"
gh variable set ACR_NAME --body "<acr-name-without-.azurecr.io>"
gh variable set RESOURCE_GROUP --body "<from terraform output resource_group_name>"
gh variable set FRONTEND_APP_NAME --body "ca-fe-<name-suffix>"
gh variable set BACKEND_APP_NAME --body "ca-be-<name-suffix>"
gh variable set BACKEND_FQDN --body "<from terraform output backend_fqdn>"
```

### Prerequisites

- The Terraform deployer identity needs `Application Administrator` role in Entra ID to create app registrations.
- The `azuread` provider authenticates using the same context as `azurerm` (e.g., `az login`).

---

## Decision Log

| # | Decision | Status | Notes |
|---|----------|--------|-------|
| D1 | Network: ACR publicly accessible for CI push | **Resolved** | No change needed — Entra-ID-only auth, public endpoint is just reachable, not open |
| D2 | Network: Container Apps deploy via ARM (no VNet needed) | **Resolved** | No change needed |
| D3 | CI triggers | **Resolved** | All PRs + push to `main`, path-ignore for .md/docs |
| D4 | CD triggers + approval gate | **Resolved** | Push to `main`/`develop` + `production` environment approval gate on build+deploy |
| D5 | Version source for revision suffix | **Resolved** | `package.json` (frontend) + `pyproject.toml` (backend), versioned independently |
| D6 | GitHub → Azure auth method | **Resolved — OIDC** | Environment-based subject (`environment:production`) — single credential covers both branches |
| D7 | Scope of CD contributor role | **Resolved** | Scoped to each Container App resource (least privilege, not RG-level) |
| D8 | Selective deployment | **Resolved** | Path detection via `dorny/paths-filter` + optional `workflow_dispatch` inputs |
| D9 | OIDC federated credential subject | **Resolved** | Environment-based (`environment:production`) — 1 credential instead of per-branch |
