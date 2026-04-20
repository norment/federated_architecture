#!/bin/bash
set -e
set -o pipefail

if [ -z "$1" ]; then
    echo "Usage: ./client_regenie_nodocker.sh <site_number>"
    exit 1
fi

SITE_NUM=$1

# Common data directory
#SITE_DIR="/home/zrahman/nvflare/data"

# Select filenames based on site number
if [ "${SITE_NUM}" -eq 1 ]; then
    SITE_DIR="/home/zrahman/nvflare/data"
    BED_PREFIX="geno_100k_1k"
    PHENO_FILE="phenotype_AD1.csv"
    COVAR_FILE="Covariates_AD1.csv"

elif [ "${SITE_NUM}" -eq 2 ]; then
    SITE_DIR="/home/zrahman/nvflare/data/simu_geno1"
    BED_PREFIX="geno_100k_snellius"
    PHENO_FILE="phenotype_AD2.csv"
    COVAR_FILE="Covariates_AD2.csv"

elif [ "${SITE_NUM}" -eq 3 ]; then
    SITE_DIR="/home/ubuntu/nvflare_local_data/FedGWAS_20260309"
    BED_PREFIX="geno_100k_ukb"
    PHENO_FILE="phenotype_AD_espen.csv"
    COVAR_FILE="Covariates_AD_espen.csv"


else
    echo "Error: unsupported site number '${SITE_NUM}'. Only 1 and 2 are defined."
    exit 1
fi

if [ ! -d "${SITE_DIR}" ]; then
    echo "Error: Data directory not found: ${SITE_DIR}"
    exit 1
fi

echo "Running REGENIE locally (no Docker) on site ${SITE_NUM}"
echo "Data dir: ${SITE_DIR}"
echo "Genotype: ${BED_PREFIX}"
echo "Pheno:    ${PHENO_FILE}"
echo "Covar:    ${COVAR_FILE}"

# Step 1
regenie \
  --step 1 \
  --bed ${SITE_DIR}/${BED_PREFIX} \
  --phenoFile ${SITE_DIR}/${PHENO_FILE} \
  --covarFile ${SITE_DIR}/${COVAR_FILE} \
  --bsize 1000 \
  --bt \
  --lowmem \
  --out ${SITE_DIR}/regenie_step1

STEP1_EXIT=$?
if [ $STEP1_EXIT -ne 0 ]; then
    echo "Step 1 failed with exit code ${STEP1_EXIT}"
    exit $STEP1_EXIT
fi

if [ ! -f "${SITE_DIR}/regenie_step1_pred.list" ]; then
    echo "Step 1 prediction file not found: ${SITE_DIR}/regenie_step1_pred.list"
    exit 1
fi

# Step 2
regenie \
  --step 2 \
  --bed ${SITE_DIR}/${BED_PREFIX} \
  --phenoFile ${SITE_DIR}/${PHENO_FILE} \
  --covarFile ${SITE_DIR}/${COVAR_FILE} \
  --bt \
  --firth --approx \
  --pred ${SITE_DIR}/regenie_step1_pred.list \
  --bsize 400 \
  --out ${SITE_DIR}/regenie_step2

STEP2_EXIT=$?
if [ $STEP2_EXIT -ne 0 ]; then
    echo "Step 2 failed with exit code ${STEP2_EXIT}"
    exit $STEP2_EXIT
fi

echo "REGENIE completed for site ${SITE_NUM}"
ls -lh ${SITE_DIR}/regenie_step1* ${SITE_DIR}/regenie_step2* 2>/dev/null

