<div align="center">

# Healthcare DevOps Platform

### Event-Driven Microservices | GitOps | SRE | Policy-as-Code

[![Azure](https://img.shields.io/badge/Microsoft_Azure-0078D4?style=for-the-badge&logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Helm](https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white)](https://helm.sh/)
[![FluxCD](https://img.shields.io/badge/Flux_CD-5468FF?style=for-the-badge&logo=flux&logoColor=white)](https://fluxcd.io/)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-00C853?style=for-the-badge)]()
[![FHIR](https://img.shields.io/badge/FHIR_R4-FF6F00?style=for-the-badge)](https://hl7.org/fhir/)

A production-grade, HIPAA-compliant healthcare system on Azure, covering infrastructure automation, GitOps delivery, observability, security, and chaos engineering.

[Architecture](#architecture) | [Quick Start](#quick-start) | [Pipelines](#cicd-pipelines) | [GitOps](#gitops) | [SRE](#sre--observability) | [Security](#security--compliance)

---

</div>

## Overview

This repository contains the full platform engineering stack for a healthcare system running on Azure. It covers every layer from infrastructure provisioning to application deployment and operational observability.

| Layer | Scope | Technologies |
|-------|-------|-------------|
| **Infrastructure** | Multi-env IaC with drift detection | Terraform modules, Bicep |
| **Orchestration** | AKS with system and application node pools | Kubernetes, Helm 3 |
| **Delivery** | Multi-stage pipelines with quality gates | Azure Pipelines, reusable templates |
| **Deployment** | Declarative GitOps with auto-reconciliation | Flux CD, Kustomize overlays |
| **Observability** | SLOs, golden signals, on-call runbooks | Azure Monitor, Grafana, Prometheus |
| **Security** | Zero-trust networking, policy-as-code, supply chain | OPA Gatekeeper, Trivy, RBAC |
| **Resilience** | Chaos experiments, disaster recovery | Azure Chaos Studio, Litmus |
| **Application** | Event-driven healthcare microservices | Python, FastAPI, React, FHIR R4 |

---

## Architecture

```
+------------------------------------------------------------------+
|                        Azure Front Door (WAF)                     |
+--------------+-----------------------------------+----------------+
               |                                   |
+--------------v---------------+   +---------------v--------------+
|     API Management Gateway   |   |        Static Web App        |
|     (rate limit, auth, JWT)  |   |    (React Healthcare UI)     |
+--------------+---------------+   +------------------------------+
               |
+--------------v----------------------------------------------+
|                    Azure Kubernetes Service                   |
|  +-----------+ +-----------+ +-------------+ +-----------+   |
|  | Patient   | | Clinical  | | Notification| | Analytics |   |
|  | Service   | | Service   | | Service     | | Service   |   |
|  +-----+-----+ +-----+-----+ +------+------+ +-----+-----+  |
|        |              |              |              |          |
|  +-----v--------------v--------------v--------------v------+  |
|  |              Azure Service Bus (Event Mesh)              |  |
|  +----------------------------------------------------------+  |
|                                                                 |
|  +----------+ +----------+ +----------+ +------------------+    |
|  | FHIR     | | AI Agent | | MCP      | | Flux CD (GitOps) |   |
|  | Proxy    | | Backend  | | Server   | | + Kustomize      |   |
|  +----------+ +----------+ +----------+ +------------------+    |
+-----------------------------------------------------------------+
        |              |              |              |
+-------v---+ +-------v---+ +-------v---+ +-------v-----------+
| PostgreSQL | | Cosmos DB | |   Redis   | | Azure OpenAI      |
| (Flex HA)  | | (Multi-   | |  (Cache)  | | (GPT-4)           |
|            | |  region)  | |           | |                    |
+------------+ +-----------+ +-----------+ +--------------------+
        |              |              |
+-------v--------------v--------------v--------------------------+
|            Azure Monitor / App Insights / Log Analytics         |
|            Grafana Dashboards / SLO Tracking / Alerts           |
+----------------------------------------------------------------+
```

---

## Project Structure

```
.
|-- .azure-pipelines/              # CI/CD Pipeline Definitions
|   |-- ci.yml                     #   Continuous Integration (build+test+scan)
|   |-- cd.yml                     #   Continuous Delivery (dev > staging > prod)
|   |-- infra.yml                  #   Infrastructure provisioning pipeline
|   +-- templates/                 #   Reusable YAML templates
|       |-- build-container.yml    #     Docker build + push to ACR
|       |-- deploy-helm.yml        #     Helm upgrade via GitOps PR
|       |-- security-scan.yml      #     Trivy + Checkov + OWASP ZAP
|       +-- run-tests.yml          #     Unit / integration / e2e tests
|
|-- infrastructure/                # Infrastructure as Code
|   |-- terraform/                 #   Terraform (primary IaC)
|   |   |-- main.tf
|   |   |-- variables.tf / outputs.tf
|   |   +-- modules/               #   10 reusable modules
|   +-- bicep/                     #   Bicep (alternative IaC)
|       |-- main.bicep
|       +-- modules/               #   12 modular components
|
|-- helm-charts/                   # Helm Charts
|   +-- healthcare-platform/       #   Umbrella chart
|       |-- Chart.yaml
|       |-- values.yaml            #     Base values
|       |-- values-dev.yaml        #     Dev overrides
|       |-- values-staging.yaml    #     Staging overrides
|       |-- values-prod.yaml       #     Production overrides
|       +-- templates/             #     K8s manifest templates
|
|-- gitops/                        # GitOps (Flux CD)
|   |-- clusters/
|   |   +-- aks-healthcare/        #   Cluster bootstrap
|   |-- infrastructure/            #   Cluster-wide infra (ingress, cert-mgr)
|   +-- apps/                      #   Application releases
|       |-- base/                  #     Kustomize base
|       +-- overlays/              #     Per-environment overlays
|           |-- dev/
|           |-- staging/
|           +-- production/
|
|-- monitoring/                    # SRE and Observability
|   |-- dashboards/                #   Grafana JSON dashboards
|   |-- alerts/                    #   Prometheus + Azure alert rules
|   |-- slo/                       #   SLO / SLI definitions
|   +-- runbooks/                  #   Incident response playbooks
|
|-- policies/                      # Policy-as-Code
|   |-- opa-gatekeeper/            #   OPA constraint templates
|   +-- azure-policy/              #   Azure Policy definitions
|
|-- security/                      # Security Automation
|   |-- network-policies/          #   K8s NetworkPolicy manifests
|   |-- rbac/                      #   Kubernetes RBAC
|   +-- supply-chain/              #   Image signing, SBOM
|
|-- chaos/                         # Chaos Engineering
|   +-- experiments/               #   Azure Chaos Studio experiments
|
|-- tests/                         # Test Suites
|   |-- integration/               #   API integration tests
|   |-- e2e/                       #   End-to-end Playwright tests
|   +-- load/                      #   k6 load tests
|
|-- docs/                          # Documentation
|   |-- architecture/              #   ADRs and diagrams
|   |-- runbooks/                  #   Operational runbooks
|   +-- onboarding/                #   Developer onboarding
|
+-- src/                           # Microservices Source
    |-- patient-service/           #   Patient CRUD + FHIR
    |-- clinical-service/          #   Clinical AI assessments
    |-- notification-service/      #   Alerts, emails, webhooks
    |-- analytics-service/         #   Reporting and dashboards
    +-- api-gateway/               #   Kong / APIM config
```

---

## Quick Start

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Azure CLI | >= 2.50 | `brew install azure-cli` |
| Terraform | >= 1.5 | `brew install terraform` |
| kubectl | >= 1.28 | `az aks install-cli` |
| Helm | >= 3.12 | `brew install helm` |
| Flux CLI | >= 2.0 | `brew install fluxcd/tap/flux` |

### Deployment

```bash
# Clone
git clone https://github.com/kushal9897/healthcare-platform-azure.git
cd healthcare-platform-azure

# Login to Azure
az login && az account set -s <SUBSCRIPTION_ID>

# Provision infrastructure
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars   # edit values
terraform init && terraform apply

# Bootstrap GitOps
flux bootstrap github \
  --owner=kushal9897 \
  --repository=healthcare-platform-azure \
  --path=gitops/clusters/aks-healthcare \
  --personal

# Apps deploy automatically via Flux reconciliation
flux get kustomizations --watch
```

Infrastructure provisioning takes roughly 25 minutes. Application deployment is handled automatically by Flux after bootstrap.

---

## CI/CD Pipelines

### Pipeline Flow

```
  Feature Branch          Main Branch           Release Tag
       |                      |                      |
       v                      v                      v
  +---------+           +---------+           +---------+
  |   CI    |           |  CI+CD  |           |  CD     |
  | lint    |           | build   |           | prod    |
  | test    |           | scan    |           | deploy  |
  | scan    |           | push    |           |         |
  +---------+           | deploy  |           +---------+
                        |  > dev  |
                        |  > stg  | (manual gate)
                        +---------+
```

### Quality Gates

| Gate | Tool | Threshold |
|------|------|-----------|
| Unit tests | pytest | 80% coverage |
| SAST | Bandit + Semgrep | 0 high/critical |
| Container scan | Trivy | 0 critical CVEs |
| IaC scan | Checkov | 100% pass |
| DAST | OWASP ZAP | 0 high alerts |
| License check | FOSSA | Approved licenses only |
| Image signing | Notation (Notary v2) | Signed images only |

---

## GitOps

All deployments happen through Git. No manual `kubectl apply` or `helm upgrade` commands.

```
Developer pushes code
       |
       v
CI pipeline builds image, pushes to ACR
       |
       v
CI opens PR to gitops/apps/overlays/<env>
  (bumps image tag in kustomization.yaml)
       |
       v
PR merged -> Flux detects change -> reconciles cluster
       |
       v
App deployed  (rollback = git revert)
```

Key benefits:
- Every deployment is a git commit with full audit trail
- Rollback is a `git revert`
- Drift detection and auto-remediation
- Environment promotion via pull request reviews

---

## SRE and Observability

### Golden Signals

| Signal | Metric | SLO Target |
|--------|--------|------------|
| **Latency** | p99 API response time | < 500ms |
| **Traffic** | Requests per second | Tracked |
| **Errors** | 5xx error rate | < 0.1% |
| **Saturation** | CPU / Memory utilization | < 75% |

### SLO Definitions

```yaml
# Patient Service
- name: patient-service-availability
  target: 99.95%
  window: 30d
  indicator: successful_requests / total_requests

- name: patient-service-latency
  target: 99.0%
  window: 30d
  indicator: requests_below_500ms / total_requests
```

### Alert Severity Levels

| Severity | Response Time | Channel | Example |
|----------|--------------|---------|---------|
| P1 - Critical | 5 min | PagerDuty + Teams | Service down, data loss |
| P2 - High | 15 min | Teams + Email | SLO burn rate > 10x |
| P3 - Medium | 1 hour | Email | Elevated error rate |
| P4 - Low | Next business day | Ticket | Certificate expiring |

---

## Security and Compliance

### Defense in Depth

```
+--------------------------------------------------+
|  Layer 1: Azure Front Door + WAF                  |
|  +----------------------------------------------+|
|  |  Layer 2: API Management (OAuth, JWT, CORS)  ||
|  |  +------------------------------------------+||
|  |  |  Layer 3: AKS Network Policies (mTLS)    |||
|  |  |  +--------------------------------------+|||
|  |  |  |  Layer 4: OPA Gatekeeper Policies     ||||
|  |  |  |  +----------------------------------+||||
|  |  |  |  |  Layer 5: Pod Security Standards  |||||
|  |  |  |  |  +------------------------------+|||||
|  |  |  |  |  |  Layer 6: Key Vault (CSI)    ||||||
|  |  |  |  |  +------------------------------+|||||
|  |  |  |  +----------------------------------+||||
|  |  |  +--------------------------------------+|||
|  |  +------------------------------------------+||
|  +----------------------------------------------+|
+--------------------------------------------------+
```

### HIPAA Technical Safeguards

| Requirement | Implementation |
|-------------|---------------|
| Access Control | Azure AD + Kubernetes RBAC + OPA |
| Audit Controls | Log Analytics + immutable audit trail |
| Integrity | SHA-256 checksums, Notary image signing |
| Authentication | MFA enforced, service mesh mTLS |
| Transmission | TLS 1.3, Private Endpoints, Private Link |
| Encryption at Rest | AES-256 via Azure Storage Service Encryption |

---

## Chaos Engineering

Predefined experiments to validate resilience under failure conditions:

| Experiment | Target | Expected Behavior |
|-----------|--------|-------------------|
| Pod Kill | patient-service | Auto-restart, zero downtime |
| AZ Failure | Node pool | Workloads reschedule to healthy zones |
| CPU Stress | clinical-service | HPA scales out, latency stays within SLO |
| DNS Failure | CoreDNS | Cached queries serve, alert fires < 2 min |
| Network Partition | Service Bus | Dead-letter queue, retry with backoff |

---

## Cost Optimization

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| Reserved Instances | 40-60% | 1-year AKS node commitment |
| Spot Node Pools | 60-80% | Batch/analytics workloads |
| Auto-scaling | Variable | HPA + Cluster Autoscaler (scale-to-zero dev) |
| Right-sizing | 20-30% | Azure Advisor recommendations automated |
| Dev auto-shutdown | 70% | Scheduled scale-down evenings/weekends |

Monthly estimate: Dev $300-500 | Staging $800-1,200 | Prod $2,500-5,000

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Cloud** | Azure (AKS, ACR, Service Bus, OpenAI, Cosmos DB, PostgreSQL, Redis, Key Vault, Front Door, APIM) |
| **IaC** | Terraform 1.5+, Bicep, ARM |
| **Orchestration** | Kubernetes 1.28, Helm 3, Kustomize |
| **GitOps** | Flux CD v2, GitHub Actions (PR automation) |
| **CI/CD** | Azure Pipelines, multi-stage YAML |
| **Observability** | Azure Monitor, Prometheus, Grafana, OpenTelemetry |
| **Security** | OPA Gatekeeper, Trivy, Checkov, Notation, Falco |
| **Chaos** | Azure Chaos Studio, Litmus |
| **Testing** | pytest, Playwright, k6, OWASP ZAP |
| **Languages** | Python 3.11, TypeScript 5, Bash |
| **Healthcare** | FHIR R4, HL7, Azure Health Data Services |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture Decision Records](docs/architecture/) | Technology selection rationale |
| [Operational Runbooks](monitoring/runbooks/) | Step-by-step incident response |
| [Developer Onboarding](docs/onboarding/) | Local setup and workflow guide |
| [Azure Deployment Guide](docs/AZURE_DEPLOYMENT_GUIDE.md) | Full deployment walkthrough |
| [DevOps Best Practices](docs/AZURE_DEVOPS_BEST_PRACTICES.md) | Standards and conventions |
| [Contributing](docs/CONTRIBUTING.md) | Code review and PR process |

---

## License

MIT -- see [LICENSE](LICENSE)
