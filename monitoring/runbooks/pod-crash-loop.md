# Runbook: Pod CrashLoopBackOff

## Alert
**Name:** `PodCrashLooping`
**Severity:** Critical
**Impact:** Service degradation or outage

## Triage Steps

### 1. Identify the Pod
```bash
kubectl get pods -n healthcare-production | grep -E "CrashLoop|Error"
```

### 2. Check Pod Events
```bash
kubectl describe pod <POD_NAME> -n healthcare-production
# Look for: Events section, Exit codes, OOMKilled
```

### 3. Check Logs
```bash
# Current attempt
kubectl logs <POD_NAME> -n healthcare-production

# Previous crash
kubectl logs <POD_NAME> -n healthcare-production --previous

# All containers in pod
kubectl logs <POD_NAME> -n healthcare-production --all-containers
```

### 4. Common Causes & Fixes

| Exit Code | Cause | Fix |
|-----------|-------|-----|
| 0 | Normal exit (liveness probe issue) | Increase `initialDelaySeconds` |
| 1 | Application error | Check logs for stack trace |
| 137 | OOMKilled | Increase memory limits |
| 139 | Segfault | Check application code |
| 143 | SIGTERM (graceful shutdown failed) | Increase `terminationGracePeriodSeconds` |

### 5. Quick Fixes
```bash
# Restart the deployment
kubectl rollout restart deployment/<DEPLOYMENT> -n healthcare-production

# Scale to 0 then back up (nuclear option)
kubectl scale deployment/<DEPLOYMENT> -n healthcare-production --replicas=0
kubectl scale deployment/<DEPLOYMENT> -n healthcare-production --replicas=3

# Rollback if caused by recent deployment
kubectl rollout undo deployment/<DEPLOYMENT> -n healthcare-production
```

## Escalation
- If unresolved after 15 min -> page on-call engineer
- If data loss suspected -> page database team
- If security incident -> follow security incident runbook
