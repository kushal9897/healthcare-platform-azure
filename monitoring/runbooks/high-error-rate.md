# Runbook: High Error Rate

## Alert
**Name:** `HighErrorRate`
**Severity:** Warning -> Critical (if > 5 min)
**SLO Impact:** Yes  -  burns error budget

## Symptoms
- Error rate exceeds 1% for a service
- Users may see 500 errors or timeouts
- Downstream services may be affected

## Triage Steps

### 1. Identify Affected Service
```bash
# Check which pods are failing
kubectl get pods -n healthcare-production -l app=<SERVICE> | grep -v Running

# Check recent events
kubectl get events -n healthcare-production --sort-by='.lastTimestamp' | head -20
```

### 2. Check Logs
```bash
# Tail logs for the failing service
kubectl logs -f deployment/<SERVICE> -n healthcare-production --tail=100

# Search for errors
kubectl logs deployment/<SERVICE> -n healthcare-production --since=10m | grep -i error
```

### 3. Check Dependencies
```bash
# PostgreSQL connectivity
kubectl exec -it deployment/<SERVICE> -n healthcare-production -- \
  python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"

# Redis connectivity
kubectl exec -it deployment/<SERVICE> -n healthcare-production -- \
  python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()"

# Azure OpenAI
kubectl exec -it deployment/<SERVICE> -n healthcare-production -- \
  curl -s https://<OPENAI_ENDPOINT>/openai/deployments/gpt-4/completions?api-version=2024-02-01 \
  -H "api-key: $AZURE_OPENAI_KEY" -H "Content-Type: application/json" \
  -d '{"prompt":"test","max_tokens":1}'
```

### 4. Check Resource Usage
```bash
kubectl top pods -n healthcare-production
kubectl top nodes
```

## Resolution

### Scenario A: OOM / Resource Exhaustion
```bash
# Scale up temporarily
kubectl scale deployment/<SERVICE> -n healthcare-production --replicas=5

# If OOMKilled, increase limits
kubectl edit deployment/<SERVICE> -n healthcare-production
# Increase memory limits
```

### Scenario B: Dependency Failure
```bash
# Check Azure service health
az resource list --resource-group rg-healthcare-ai --output table

# Restart the service to re-establish connections
kubectl rollout restart deployment/<SERVICE> -n healthcare-production
```

### Scenario C: Bad Deployment
```bash
# Check recent deployments
kubectl rollout history deployment/<SERVICE> -n healthcare-production

# Rollback to previous version
kubectl rollout undo deployment/<SERVICE> -n healthcare-production

# Or via GitOps (preferred):
cd gitops/apps/overlays/production
git revert HEAD
git push
```

## Post-Incident
1. Update this runbook with new findings
2. Create incident report
3. Schedule blameless post-mortem
4. Update SLO error budget tracking
5. Create follow-up tickets for prevention
