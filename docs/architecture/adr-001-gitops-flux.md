# ADR-001: Use Flux CD for GitOps Deployments

## Status
**Accepted**  -  2024-01-15

## Context
We need a deployment strategy for the healthcare platform on AKS that provides:
- Full audit trail (HIPAA requirement)
- Easy rollback capability
- Drift detection and auto-remediation
- Multi-environment promotion (dev -> staging -> production)
- Declarative, version-controlled deployments

Options considered:
1. **kubectl apply** via Azure Pipelines (imperative)
2. **Helm upgrade** via Azure Pipelines (semi-declarative)
3. **Flux CD** (pull-based GitOps)
4. **ArgoCD** (pull-based GitOps)

## Decision
We chose **Flux CD v2** for GitOps deployments.

## Rationale
- **Audit trail**: Every deployment is a git commit  -  satisfies HIPAA audit requirements
- **Rollback**: `git revert` rolls back a deployment, no cluster access needed
- **Drift detection**: Flux continuously reconciles desired state from git with actual cluster state
- **CNCF graduated project**: Production-ready, well-maintained
- **Native Kustomize support**: Works with our overlay-based environment strategy
- **Azure integration**: First-class AKS support, Azure DevOps notifications
- **Lower resource footprint** compared to ArgoCD (no UI server needed)

## Consequences
- Pipeline no longer runs `kubectl apply` directly  -  it commits to the gitops directory
- All cluster changes must go through git (enforced by RBAC)
- Developers need to understand Kustomize overlay patterns
- Drift is auto-healed, which means manual `kubectl` changes are reverted
