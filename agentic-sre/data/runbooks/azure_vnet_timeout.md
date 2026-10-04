#### 3. Populate `data/runbooks/azure_vnet_timeout.md`

```powershell
Set-Content -Path data/runbooks/azure_vnet_timeout.md -Value @"
# Runbook: Azure VNet Peering & Subnet Timeout Issues

## Incident Overview
Timeouts occurring between microservices across different Virtual Networks (VNets) or subnets in Azure. Typically caused by Network Security Group (NSG) misconfigurations, missing UDRs (User Defined Routes), or broken VNet peering status.

## Failure Signatures
- Error message: `Connection timed out`, `ETIMEDOUT`, `504 Gateway Timeout`
- Intermittent connectivity losses across regional boundaries.
- Azure Network Watcher IP Flow Verify returns `Access denied`.

## Diagnostic Steps
1. Verify VNet Peering state in Azure Portal or via CLI:
   `az network vnet peering list -g <rg-name> --vnet-name <vnet-name>`
2. Test connection with Network Watcher:
   `az network watcher test-connectivity -g <rg-name> --source-resource <src-id> --dest-resource <dest-id>`
3. Inspect NSG rules applied to both source and target subnets for denied inbound/outbound rules on required ports.

## Remediation & Fixes
- **Peering Sync**: If peering state is `Disconnected`, trigger a sync or re-create peering.
- **NSG Rule Fix**: Add explicit `Allow` rule for source CIDR to destination port on priority < 1000.
- **Route Table**: Ensure UDR has `0.0.0.0/0` or explicit target IP routing to Next Hop (Virtual Appliance / Azure Firewall).

## Preventative Actions
- Implement Azure Firewall policy validation in CI/CD infrastructure pipelines (Terraform/Bicep).
- Set up Azure Monitor alerts for Network Security Group flow log drops.
"@