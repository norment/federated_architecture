# Federated GWAS Job Run Guide

This project runs a 2-client NVFlare GWAS workflow:
- Client 1: `snellius` (local REGENIE, AD2 files)
- Client 2: `tsd` (TSD wrapper REGENIE, reads from `work_dir/data`, writes to `work_dir/out`)
- Aggregation: GWAMA
- Final local outputs: `./wamma_out`

## 1) Prerequisites

- Python environment with NVFlare dependencies available.
- REGENIE available on client environments.
- GWAMA available at:
  - `/home/ubuntu/miniconda3/envs/flare/bin/GWAMA`
- TSD wrapper config file present:
  - `tsd_wrapper_config.yml`

If `tsd_wrapper_config.yml` does not exist, create it from template:

```bash
cp tsd_wrapper_config.yml.template tsd_wrapper_config.yml
```

## 2) Verify TSD Config

Open `tsd_wrapper_config.yml` and verify at least:
- `project`, `username`
- `import_dir`, `export_dir`
- `work_dir` (for example: `/cluster/project/p33/users/mohammadzr/flare/test1`)

Expected TSD layout for each run:
- input files in: `work_dir/data`
- intermediate outputs in: `work_dir/out`

## 3) Start NVFlare Server and Clients

From separate terminals:

### Server

```bash
cd workspace/nrec_server/prod_00/158.39.75.142/startup
bash start.sh
```

### Client: snellius

```bash
cd workspace/nrec_server/prod_00/snellius/startup
bash start.sh
```

### Client: tsd

```bash
cd workspace/nrec_server/prod_00/tsd/startup
bash start.sh
```

## 4) Submit and Run the Final Job

From project root (`test2`):

```bash
export REGENIE_TSD_CONFIG=/mnt/data/home/ubuntu/zillur/federated_trip/project1/test2/tsd_wrapper_config.yml
python3 hunt_job.py --n_clients 2 --num_rounds 1 --output_dir ./wamma_out
```

## 5) Check Final Outputs

After completion, check:

```bash
ls -lh wamma_out
```

Expected files include:
- `site1_snellius_regenie_step2_AD.regenie`
- `site2_tsd_regenie_step2_AD.regenie`
- `site1_snellius_gwama.txt`
- `site2_tsd_gwama.txt`
- `gwama.in`, `gwama.out`, `gwama.log.out`, `gwama.gc.out`, `gwama.err.out`

Note:
- Job artifacts are also stored in the transfer bundle under:
  - `workspace/nrec_server/prod_00/zillur@biostat.com/transfer/<job_id>/...`
- `hunt_job.py` now syncs the server bundle results into your local `wamma_out` automatically.

## 6) Stop Services (Optional)

```bash
bash workspace/nrec_server/prod_00/158.39.75.142/startup/stop_fl.sh
bash workspace/nrec_server/prod_00/snellius/startup/stop_fl.sh
bash workspace/nrec_server/prod_00/tsd/startup/stop_fl.sh
```

## 7) Common Troubleshooting

- `REGENIE_TSD_CONFIG is required`:
  - Export `REGENIE_TSD_CONFIG` before running `hunt_job.py`.
- Empty local `wamma_out` after run:
  - Re-run with updated `hunt_job.py` (result sync is automatic).
  - Check transfer bundle path shown by `run.get_result()`.
- TLS handshake warnings (`CERTIFICATE_VERIFY_FAILED`) during submission:
  - If job still reaches `FINISHED:COMPLETED`, outputs are generally valid.
  - If submission fails, verify startup kit cert/key/CA files under `workspace/.../zillur@biostat.com/startup`.
