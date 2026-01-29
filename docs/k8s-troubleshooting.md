# Kubernetes Troubleshooting Guide for Chameleon-SRE

This document contains troubleshooting knowledge for the autonomous SRE agent.

## Pod States and Common Issues

### Running
**Status**: Pod is executing successfully.
**Action**: No action needed. Continue monitoring.

### Pending
**Status**: Scheduler cannot place the pod.

**Common Causes**:
1. Insufficient cluster resources (CPU/memory)
2. No nodes match nodeSelector/affinity rules
3. PersistentVolume not available
4. Image pull in progress

**Diagnostic Commands**:
```bash
kubectl describe pod <pod-name>
kubectl get events --field-selector involvedObject.name=<pod-name>
kubectl describe nodes
```

**Auto-Remediation**:
- If resource issue: Alert engineer (cannot auto-scale)
- If nodeSelector: Suggest removing constraint
- If PVC: Check PV status and recommend manual review

---

### CrashLoopBackOff
**Status**: Container keeps crashing after starting.

**Common Causes**:
1. Application bug (most common)
2. Missing configuration (ConfigMap/Secret)
3. Resource limits exceeded
4. Failed health checks

**Diagnostic Commands**:
```bash
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
kubectl describe pod <pod-name>
kubectl get configmaps
kubectl get secrets
```

**Auto-Remediation Steps**:
1. Check logs for error patterns
2. Verify all ConfigMaps/Secrets exist
3. If missing config: Create from known template or alert engineer
4. If resource issue: Recommend increasing limits
5. Restart deployment: `kubectl rollout restart deployment/<name>`

---

### ImagePullBackOff
**Status**: Cannot pull container image.

**Common Causes**:
1. Image does not exist (typo or deleted)
2. Private registry without credentials
3. Network issues
4. Registry rate limiting

**Diagnostic Commands**:
```bash
kubectl describe pod <pod-name>
kubectl get pod <pod-name> -o yaml | grep image:
kubectl get secrets | grep docker
```

**Auto-Remediation Steps**:
1. Verify image name and tag
2. Check if imagePullSecret exists
3. If private registry: Ensure secret is created and referenced
4. Alert engineer if registry is unreachable

---

### OOMKilled (Out of Memory)
**Status**: Container exceeded memory limit.

**Diagnostic Commands**:
```bash
kubectl describe pod <pod-name>
kubectl top pod <pod-name>
kubectl get pod <pod-name> -o yaml | grep -A 5 resources:
```

**Auto-Remediation**:
1. Check actual memory usage vs. limit
2. Recommend increasing memory limit
3. Suggest reviewing application memory leaks
4. Do NOT automatically increase limits (requires engineer approval)

---

### Evicted
**Status**: Pod was evicted due to node pressure.

**Common Causes**:
1. Node running out of disk space
2. Node memory pressure
3. Node CPU pressure

**Diagnostic Commands**:
```bash
kubectl describe node <node-name>
kubectl get pod <pod-name> -o yaml | grep reason:
```

**Auto-Remediation**:
1. Alert engineer about node issues
2. Recommend node cleanup or scaling
3. Delete evicted pods: `kubectl delete pod <pod-name>`

---

## Deployment Strategies

### Rolling Update
Default strategy. Updates pods gradually.

**Commands**:
```bash
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>  # Rollback
```

### Recreate
Deletes all old pods before creating new ones.

**Use Case**: When running two versions simultaneously is not possible.

---

## Service and Networking Issues

### Service Not Accessible

**Diagnostic Commands**:
```bash
kubectl get svc
kubectl describe svc <service-name>
kubectl get endpoints <service-name>
kubectl get pods -l <label-selector>
```

**Common Issues**:
1. Service selector doesn't match pod labels
2. No healthy pods backing the service
3. Port mismatch
4. NetworkPolicy blocking traffic

---

## ConfigMap and Secret Management

### Best Practices
1. Use ConfigMaps for non-sensitive configuration
2. Use Secrets for credentials and keys
3. Mount as volumes (not environment variables for large configs)
4. Restart deployments after updating: `kubectl rollout restart deployment/<name>`

### Common Issues
- Pod references non-existent ConfigMap/Secret → CrashLoopBackOff
- ConfigMap updated but pod not restarted → Old config still in use

---

## Resource Management

### Resource Requests vs. Limits

**Requests**: Guaranteed resources (used for scheduling)
**Limits**: Maximum resources (hard cap)

**Best Practices**:
- Set requests = typical usage
- Set limits = maximum acceptable usage
- CPU: Throttled when limit exceeded
- Memory: Pod killed when limit exceeded

### Example
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

---

## Health Checks

### Liveness Probe
Determines if container is alive. If fails → restart container.

### Readiness Probe
Determines if container is ready to serve traffic. If fails → remove from service endpoints.

### Startup Probe
Gives slow-starting containers time to start. Disables liveness/readiness during startup.

### Example
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Logs and Events

### Viewing Logs
```bash
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>  # Multi-container pod
kubectl logs <pod-name> --previous  # Previous container instance
kubectl logs <pod-name> --tail=50  # Last 50 lines
kubectl logs -f <pod-name>  # Follow (stream)
```

### Viewing Events
```bash
kubectl get events --sort-by='.lastTimestamp'
kubectl get events --field-selector involvedObject.name=<pod-name>
kubectl get events --field-selector type=Warning
```

---

## Emergency Procedures

### Delete Stuck Pod
```bash
kubectl delete pod <pod-name> --grace-period=0 --force
```

### Cordon Node (Prevent New Pods)
```bash
kubectl cordon <node-name>
```

### Drain Node (Evict All Pods)
```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
```

### Restart Deployment
```bash
kubectl rollout restart deployment/<deployment-name>
```

---

## Safety Guidelines for Autonomous Operations

### ✅ SAFE Operations (Agent Can Execute)
- `kubectl get <resource>`
- `kubectl describe <resource>`
- `kubectl logs <pod>`
- `kubectl top <resource>`
- `kubectl rollout restart deployment/<name>`
- `kubectl create configmap` (after validation)
- `kubectl delete pod` (single pod, not --all)

### ⚠️ REQUIRES CONFIRMATION
- `kubectl scale deployment/<name>`
- `kubectl delete deployment/<name>`
- `kubectl patch <resource>`
- `kubectl apply -f <file>`

### 🚫 FORBIDDEN (Never Execute)
- `kubectl delete namespace`
- `kubectl delete --all`
- `kubectl delete pv/pvc` (data loss)
- Command chaining with `&&` or `|`
- Anything affecting multiple resources at once

---

**Last Updated**: 2026-01-29
**Version**: 1.0
**Maintained By**: Chameleon-SRE Knowledge Base
