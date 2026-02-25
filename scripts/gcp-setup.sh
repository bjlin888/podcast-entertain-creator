#!/usr/bin/env bash
# One-time GCP infrastructure setup for Podcast Creator.
# Required env vars:
#   GCP_PROJECT_ID    — GCP project ID
#   GEMINI_API_KEY    — Gemini API key (stored in Secret Manager)
#   GITHUB_OWNER      — GitHub username/org owning the repo
# Optional env vars:
#   ANTHROPIC_API_KEY — Anthropic API key (stored in Secret Manager)
#   GCP_REGION        — Region (default: asia-east1)
#   GCP_REPO          — Artifact Registry repo name (default: podcast-creator)
#   GCP_SERVICE       — Cloud Run service name (default: podcast-creator)
#   GITHUB_REPO       — GitHub repo name (default: podcast-entertain-creator)

set -euo pipefail

# ---------------------------------------------------------------------------
# Validate required env vars
# ---------------------------------------------------------------------------
missing=()
for var in GCP_PROJECT_ID GEMINI_API_KEY GITHUB_OWNER; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("$var")
  fi
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ERROR: Missing required environment variables: ${missing[*]}" >&2
  echo "" >&2
  echo "Usage:" >&2
  echo "  export GCP_PROJECT_ID=my-project" >&2
  echo "  export GEMINI_API_KEY=AIza..." >&2
  echo "  export GITHUB_OWNER=myuser" >&2
  echo "  export ANTHROPIC_API_KEY=sk-ant-...  # optional" >&2
  echo "  bash scripts/gcp-setup.sh" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REGION="${GCP_REGION:-asia-east1}"
REPO="${GCP_REPO:-podcast-creator}"
SERVICE="${GCP_SERVICE:-podcast-creator}"
GH_REPO="${GITHUB_REPO:-podcast-entertain-creator}"

echo "=== GCP Setup for Podcast Creator ==="
echo "  Project:  ${GCP_PROJECT_ID}"
echo "  Region:   ${REGION}"
echo "  AR Repo:  ${REPO}"
echo "  Service:  ${SERVICE}"
echo "  GitHub:   ${GITHUB_OWNER}/${GH_REPO}"
echo ""

# ---------------------------------------------------------------------------
# 1. Set project & enable APIs
# ---------------------------------------------------------------------------
echo ">>> Setting project and enabling APIs..."
gcloud config set project "${GCP_PROJECT_ID}"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

# ---------------------------------------------------------------------------
# 2. Create Artifact Registry repository
# ---------------------------------------------------------------------------
echo ">>> Creating Artifact Registry repo: ${REPO}..."
if gcloud artifacts repositories describe "${REPO}" --location="${REGION}" &>/dev/null; then
  echo "    (already exists, skipping)"
else
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}"
fi

# ---------------------------------------------------------------------------
# 3. Create secrets in Secret Manager
# ---------------------------------------------------------------------------
echo ">>> Creating Secret Manager secrets..."

create_or_update_secret() {
  local name="$1" value="$2"
  if gcloud secrets describe "${name}" &>/dev/null; then
    echo "    Secret '${name}' exists, adding new version..."
    echo -n "${value}" | gcloud secrets versions add "${name}" --data-file=-
  else
    echo "    Creating secret '${name}'..."
    echo -n "${value}" | gcloud secrets create "${name}" --data-file=-
  fi
}

create_or_update_secret "gemini-api-key" "${GEMINI_API_KEY}"

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  create_or_update_secret "anthropic-api-key" "${ANTHROPIC_API_KEY}"
else
  echo "    Skipping anthropic-api-key (ANTHROPIC_API_KEY not set)"
fi

# ---------------------------------------------------------------------------
# 4. Grant IAM roles to service accounts
# ---------------------------------------------------------------------------
PROJECT_NUMBER=$(gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')

# Cloud Build default SA (used by gcloud builds submit)
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo ">>> Granting IAM roles to compute default SA (${COMPUTE_SA})..."
for role in roles/run.admin roles/secretmanager.secretAccessor roles/iam.serviceAccountUser roles/storage.objectAdmin roles/artifactregistry.writer roles/logging.logWriter; do
  echo "    Binding ${role}..."
  gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="${role}" \
    --condition=None \
    --quiet
done

# ---------------------------------------------------------------------------
# 5. Ensure GitHub repo exists and code is pushed
# ---------------------------------------------------------------------------
echo ">>> Checking GitHub repository..."

if ! command -v gh &>/dev/null; then
  echo "    WARNING: gh CLI not found. Skipping GitHub repo setup." >&2
  echo "    Install: https://cli.github.com/" >&2
else
  # Check if repo exists on GitHub
  if gh repo view "${GITHUB_OWNER}/${GH_REPO}" &>/dev/null; then
    echo "    GitHub repo ${GITHUB_OWNER}/${GH_REPO} already exists."
  else
    echo "    Creating GitHub repo ${GITHUB_OWNER}/${GH_REPO}..."
    gh repo create "${GITHUB_OWNER}/${GH_REPO}" --public --source=. --remote=origin --push
    echo "    GitHub repo created and code pushed."
  fi

  # Ensure git remote is set
  if ! git remote get-url origin &>/dev/null; then
    echo "    Adding git remote 'origin'..."
    git remote add origin "https://github.com/${GITHUB_OWNER}/${GH_REPO}.git"
  fi

  # Check for uncommitted changes
  if [[ -n "$(git status --porcelain)" ]]; then
    echo ""
    echo "    WARNING: You have uncommitted changes."
    echo "    Please commit and push before creating a Cloud Build trigger."
    echo "    Run:  git add -A && git commit -m 'your message' && git push -u origin main"
    echo ""
  else
    # Push if not yet pushed
    if ! git rev-parse --verify origin/main &>/dev/null 2>&1; then
      echo "    Pushing to origin/main..."
      git push -u origin main
    else
      echo "    origin/main is up to date."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 6. Create Cloud Build trigger (GitHub push to main)
# ---------------------------------------------------------------------------
echo ">>> Creating Cloud Build trigger..."
TRIGGER_NAME="${SERVICE}-main"

if gcloud builds triggers describe "${TRIGGER_NAME}" --region="${REGION}" &>/dev/null; then
  echo "    Trigger '${TRIGGER_NAME}' already exists, skipping"
else
  echo ""
  echo "    Cloud Build 2nd-gen triggers require a GitHub App connection."
  echo "    Before creating the trigger, you must connect your GitHub repo"
  echo "    in the Google Cloud Console:"
  echo ""
  echo "    1. Go to: https://console.cloud.google.com/cloud-build/repositories/2nd-gen?project=${GCP_PROJECT_ID}"
  echo "    2. Click 'Link a repository' and follow the GitHub App install flow"
  echo "    3. Select repository: ${GITHUB_OWNER}/${GH_REPO}"
  echo ""

  # Try to find the 2nd-gen repository connection
  echo "    Searching for linked repository..."
  REPO_LINK=$(gcloud builds repositories list \
    --region="${REGION}" \
    --connection="*" \
    --filter="remoteUri~'github.com/${GITHUB_OWNER}/${GH_REPO}'" \
    --format='value(name)' 2>/dev/null | head -1)

  if [[ -n "${REPO_LINK}" ]]; then
    echo "    Found linked repository: ${REPO_LINK}"
    gcloud builds triggers create github \
      --name="${TRIGGER_NAME}" \
      --repository="${REPO_LINK}" \
      --branch-pattern='^main$' \
      --build-config=cloudbuild.yaml \
      --region="${REGION}" \
      && echo "    Trigger '${TRIGGER_NAME}' created successfully." \
      || echo "    ERROR: Trigger creation failed. Check the error above."
  else
    echo "    No linked repository found."
    echo "    After linking the repo in Console, re-run this script or create the trigger manually:"
    echo ""
    echo "    gcloud builds triggers create github \\"
    echo "      --name=${TRIGGER_NAME} \\"
    echo "      --repository=projects/${GCP_PROJECT_ID}/locations/${REGION}/connections/<CONNECTION>/repositories/${GH_REPO} \\"
    echo "      --branch-pattern='^main\$' \\"
    echo "      --build-config=cloudbuild.yaml \\"
    echo "      --region=${REGION}"
    echo ""
  fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. If Cloud Build trigger was not created, link your GitHub repo at:"
echo "     https://console.cloud.google.com/cloud-build/repositories/2nd-gen?project=${GCP_PROJECT_ID}"
echo "     Then re-run this script."
echo "  2. Deploy manually:  bash scripts/gcp-deploy.sh"
echo "  3. Or push to main to trigger auto-deploy"
