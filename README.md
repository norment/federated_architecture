# federated_architecture

NVFLARE connectors and other federated infrastructure

# Relevant google docs and spreadsheets

* [Federated analysis notes](https://docs.google.com/document/d/1GXTNEM4xV8B8EXIqsBx1SABcf-_82UnD5OT2Bu1KVKY/edit?tab=t.0)
* [Federated analysis studies](https://docs.google.com/spreadsheets/d/1vUDLtJvQESbyEKG9y48WJQ8VzD6K-hYIJnLNc8Wauqs/edit?gid=0#gid=0) spreadsheets
* [Federated analysis use-cases](https://docs.google.com/spreadsheets/d/1vUDLtJvQESbyEKG9y48WJQ8VzD6K-hYIJnLNc8Wauqs/edit?gid=968194630#gid=968194630) - same spreadsheet as above, but second tab

# NVFlare server

* Oslo: NREC
* JCVI: TBD

# Site-specific codes

* UK Biobank and DX: see [ukb](ukb) folder
* TSD: https://github.com/precimed/tsd_hpc_api
* HUNT: https://github.com/lcmoore/FedFEMA/tree/huntcloud/HUNT_Cloud
* EADB - https://github.com/amorris28/eadb-ad-prediction/tree/main/federation
* Snellius: see [here](https://github.com/lcmoore/FedFEMA/tree/real_world_setup/Snellius/real_world)
* JCVI "simulated" clients (nvflare native; ssh / slurm with or without VPN) - TBD(Lance, Pravesh) point to the codes

# Framework examples

* NVFLARE wrapper around SLURM api: see [here](https://github.com/NVIDIA/NVFlare/blob/main/examples/advanced/llm_hf/MULTINODE.md)

# Use cases

* Federated GWAS - https://github.com/precimed/FedGen