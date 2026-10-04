Set-Content -Path data/runbooks/k8s_oomkilled.md -Value @"
# Runbook: Kubernetes OOMKilled (Exit Code 137)

## Incident Overview
An OOMKilled error indicates that a container exceeded its allocated memory limit defined in the Kubernetes pod spec. The Linux kernel OOM killer terminates the process to prevent node instability.

## Failure Signatures
- Pod status: `OOMKilled` or `CrashLoopBackOff`
- Exit Code: `137`
- Kernel log signature: `Memory cgroup out of memory: Kill process`

## Diagnostic Steps
1. Identify affected pod: `kubectl get pods -n <namespace> -o wide`
2. Describe pod to check memory limits: `kubectl describe pod <pod-name> -n <namespace>`
3. Check recent memory usage trends via Prometheus or Grafana.
4. Inspect previous logs before termination: `kubectl logs <pod-name> -n <namespace> --previous`

## Remediation & Fixes
- **Immediate Fix**: Temporarily bump memory limits in deployment spec:
  ```yaml
  resources:
    limits:
      memory: "2Gi"
    requests:
      memory: "1Gi"