# Developer Onboarding Guide

Get started contributing to the Healthcare DevOps Platform in 30 minutes.

## Prerequisites

| Tool | Install |
|------|---------|
| Azure CLI | `brew install azure-cli` |
| kubectl | `az aks install-cli` |
| Helm 3 | `brew install helm` |
| Terraform | `brew install terraform` |
| Flux CLI | `brew install fluxcd/tap/flux` |
| Python 3.11 | `brew install python@3.11` |
| Node.js 20 | `brew install node@20` |
| k6 | `brew install k6` |

## Quick Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/kushal9897/healthcare-platform-azure.git
cd healthcare-platform-azure

# 2. Login to Azure
az login

# 3. Connect to dev AKS cluster
az aks get-credentials --resource-group rg-healthcare-ai-dev --name aks-healthcare-ai-dev

# 4. Verify connection
kubectl get pods -n healthcare-dev
```

## Local Development

### Run a service locally
```bash
cd src/patient-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Run tests
```bash
pytest tests/ -v --cov=. --cov-report=term
```

### Build container locally
```bash
docker build -t patient-service:dev src/patient-service/
docker run -p 8000:8000 patient-service:dev
```

## Project Structure Cheat Sheet

| Directory | What's in it | When to edit |
|-----------|-------------|--------------|
| `src/` | Microservice source code | Adding features / fixing bugs |
| `.azure-pipelines/` | CI/CD pipeline definitions | Changing build/deploy process |
| `helm-charts/` | Helm chart & values | Changing K8s configuration |
| `gitops/` | Flux CD & Kustomize overlays | Changing per-env settings |
| `infrastructure/terraform/` | Azure resource definitions | Adding/changing cloud resources |
| `monitoring/` | Dashboards, alerts, SLOs | Changing observability |
| `policies/` | OPA & Azure Policy | Changing security policies |
| `tests/` | Integration & load tests | Adding test coverage |

## Git Workflow

```
main <- (protected, requires PR + 1 approval)
  +-- feature/TICKET-123-description <- (your working branch)
```

1. Create branch: `git checkout -b feature/TICKET-123-add-patient-search`
2. Make changes, commit often
3. Push: `git push origin feature/TICKET-123-add-patient-search`
4. Open PR -> CI runs automatically -> Get review -> Merge
5. CD pipeline auto-deploys to dev -> manual promotion to staging/prod

## Useful Commands

```bash
# View pods and their status
kubectl get pods -n healthcare-dev -o wide

# Stream logs from a service
kubectl logs -f deployment/patient-service -n healthcare-dev

# Port-forward for local testing
kubectl port-forward svc/patient-service 8000:8000 -n healthcare-dev

# Check Flux sync status
flux get kustomizations

# Check Helm releases
helm list -n healthcare-dev

# Run load tests against dev
k6 run --env BASE_URL=https://dev-api.healthcare.internal tests/load/healthcare-load-test.js
```

## Need Help?
- Check runbooks: `monitoring/runbooks/`
- Check ADRs for design decisions: `docs/architecture/`
- Open a GitHub issue
