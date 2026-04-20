# ADR-002: Helm Charts with Kustomize Overlays for Environment Management

## Status
**Accepted**  -  2024-01-20

## Context
We need a strategy to manage Kubernetes manifests across dev, staging, and production environments with different:
- Replica counts and resource limits
- Image registries and tags
- Feature flags and configuration
- Network policies and security controls

## Decision
Use **Helm charts** for templating and packaging, with **Kustomize overlays** for per-environment customization.

## Rationale
- **Helm**: Provides a single umbrella chart with dependency management, versioning, and rollback
- **Kustomize**: Native to kubectl, no extra tooling; clean overlay model for environment differences
- **Combined**: Helm generates the base manifests, Kustomize patches environment-specific values
- **Flux integration**: Flux natively supports both HelmRelease and Kustomization resources

## Structure
```
helm-charts/healthcare-platform/
|-- values.yaml          # Base (shared) values
|-- values-dev.yaml      # Dev overrides
|-- values-staging.yaml  # Staging overrides
+-- values-prod.yaml     # Production overrides

gitops/apps/
|-- base/                # Kustomize base
+-- overlays/
    |-- dev/             # Dev patches (replicas=1, small resources)
    |-- staging/         # Staging patches
    +-- production/      # Prod patches (replicas=3, PDBs, anti-affinity)
```

## Consequences
- Two layers of configuration (Helm values + Kustomize patches) can be complex
- Team must understand both Helm and Kustomize concepts
- Clear separation of concerns: Helm for application packaging, Kustomize for environment tuning
