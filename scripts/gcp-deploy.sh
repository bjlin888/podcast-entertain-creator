#!/usr/bin/env bash
# Manual deploy to Cloud Run (without Cloud Build trigger).
# Builds via Cloud Build, pushes to Artifact Registry, deploys to Cloud Run.
#
# Required env vars:
#   GCP_PROJECT_ID — GCP project ID
# Optional env vars:
#   GCP_REGION     — Region (default: asia-east1)
#   GCP_REPO       — Artifact Registry repo name (default: podcast-creator)
#   GCP_SERVICE    — Cloud Run service name (default: podcast-creator)
#   CORS_ORIGINS   — Comma-separated allowed origins (auto-detected from Cloud Run URL if empty)
#   IMAGE_TAG      — Image tag (default: git short SHA or "latest")
#   GCS_BUCKET     — Cloud Storage bucket for data persistence (default: ${GCP_PROJECT_ID}-podcast-data)

set -euo pipefail

# ---------------------------------------------------------------------------
# Validate required env vars
# ---------------------------------------------------------------------------
if [[ -z "${GCP_PROJECT_ID:-}" ]]; then
  echo "ERROR: GCP_PROJECT_ID is required" >&2
  echo "" >&2
  echo "Usage:" >&2
  echo "  export GCP_PROJECT_ID=my-project" >&2
  echo "  bash scripts/gcp-deploy.sh" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REGION="${GCP_REGION:-asia-east1}"
REPO="${GCP_REPO:-podcast-creator}"
SERVICE="${GCP_SERVICE:-podcast-creator}"
TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}"
IMAGE="${REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${REPO}/${SERVICE}:${TAG}"
DATA_BUCKET="${GCS_BUCKET:-${GCP_PROJECT_ID}-podcast-data}"

echo "=== Deploying Podcast Creator to Cloud Run ==="
echo "  Project: ${GCP_PROJECT_ID}"
echo "  Region:  ${REGION}"
echo "  Image:   ${IMAGE}"
echo "  Tag:     ${TAG}"
echo "  Bucket:  ${DATA_BUCKET}"
echo ""

# ---------------------------------------------------------------------------
# 1. Set project
# ---------------------------------------------------------------------------
gcloud config set project "${GCP_PROJECT_ID}"

# ---------------------------------------------------------------------------
# 2. Build with Cloud Build (uses free tier minutes)
# ---------------------------------------------------------------------------
echo ">>> Building image with Cloud Build..."
gcloud builds submit \
  --tag="${IMAGE}" \
  --region="${REGION}" \
  --quiet

# ---------------------------------------------------------------------------
# 3. Deploy to Cloud Run
# ---------------------------------------------------------------------------
echo ">>> Deploying to Cloud Run..."

# Auto-detect CORS_ORIGINS from existing service URL if not set
if [[ -z "${CORS_ORIGINS:-}" ]]; then
  SERVICE_URL=$(gcloud run services describe "${SERVICE}" \
    --region="${REGION}" \
    --format='value(status.url)' 2>/dev/null || true)
  if [[ -n "${SERVICE_URL}" ]]; then
    CORS_ORIGINS="${SERVICE_URL}"
    echo "    Auto-detected CORS_ORIGINS: ${CORS_ORIGINS}"
  else
    CORS_ORIGINS="*"
    echo "    WARNING: No existing service found. Using CORS_ORIGINS=* (update after first deploy)"
  fi
fi

# Build secrets flag — some secrets are optional
SECRETS="GEMINI_API_KEY=gemini-api-key:latest,ENCRYPTION_KEY=encryption-key:latest"
if gcloud secrets describe anthropic-api-key &>/dev/null; then
  SECRETS="${SECRETS},ANTHROPIC_API_KEY=anthropic-api-key:latest"
else
  echo "    Note: anthropic-api-key secret not found, skipping"
fi

gcloud run deploy "${SERVICE}" \
  --image="${IMAGE}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1 \
  --execution-environment=gen2 \
  --set-secrets="${SECRETS}" \
  --update-env-vars="CORS_ORIGINS=${CORS_ORIGINS}" \
  --add-volume=name=data-vol,type=cloud-storage,bucket="${DATA_BUCKET}" \
  --add-volume-mount=volume=data-vol,mount-path=/app/data \
  --quiet

# ---------------------------------------------------------------------------
# 4. Print result
# ---------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "${SERVICE}" \
  --region="${REGION}" \
  --format='value(status.url)')

echo ""
echo "=== Deploy complete ==="
echo "  URL: ${SERVICE_URL}"
echo "  Health: ${SERVICE_URL}/health"
echo ""

# Remind to update CORS if it was wildcard
if [[ "${CORS_ORIGINS}" == "*" ]]; then
  echo "IMPORTANT: Update CORS_ORIGINS to the actual URL:"
  echo "  export CORS_ORIGINS=${SERVICE_URL}"
  echo "  bash scripts/gcp-deploy.sh"
fi
