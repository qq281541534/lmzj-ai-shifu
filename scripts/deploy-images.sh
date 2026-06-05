#!/usr/bin/env bash
# Pull-only production deploy for lmzj-ai-shifu.
#
# The production server NEVER builds images. It pulls immutable full-SHA images
# from the company registry and recreates the stack with a parameterized
# production compose file. See lmzj-docs/ai-devops-operating-handbook.md.
#
# Required environment variables:
#   LMZJ_IMAGE_TAG        Full 40-char commit SHA to deploy.
#   LMZJ_REGISTRY         Registry host (e.g. registry.cn-beijing.aliyuncs.com).
#   LMZJ_IMAGE_NAMESPACE  Namespace/repo prefix (e.g. ai-shifu).
#   LMZJ_DEPLOY_PATH      Directory holding docker-compose.prod.yml and .env.
# Optional:
#   LMZJ_API_IMAGE_NAME       Default: lmzj-ai-shifu-api
#   LMZJ_COOK_WEB_IMAGE_NAME  Default: lmzj-ai-shifu-cook-web

set -euo pipefail

: "${LMZJ_IMAGE_TAG:?LMZJ_IMAGE_TAG (full 40-char SHA) is required}"
: "${LMZJ_REGISTRY:?LMZJ_REGISTRY is required}"
: "${LMZJ_IMAGE_NAMESPACE:?LMZJ_IMAGE_NAMESPACE is required}"
: "${LMZJ_DEPLOY_PATH:?LMZJ_DEPLOY_PATH is required}"

API_IMAGE_NAME="${LMZJ_API_IMAGE_NAME:-lmzj-ai-shifu-api}"
COOK_WEB_IMAGE_NAME="${LMZJ_COOK_WEB_IMAGE_NAME:-lmzj-ai-shifu-cook-web}"

# Reject non-immutable tags. Production only accepts a full 40-char commit SHA.
if [[ ! "${LMZJ_IMAGE_TAG}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "ERROR: LMZJ_IMAGE_TAG must be a full 40-char commit SHA, got '${LMZJ_IMAGE_TAG}'" >&2
  exit 1
fi

API_IMAGE="${LMZJ_REGISTRY}/${LMZJ_IMAGE_NAMESPACE}/${API_IMAGE_NAME}:${LMZJ_IMAGE_TAG}"
COOK_WEB_IMAGE="${LMZJ_REGISTRY}/${LMZJ_IMAGE_NAMESPACE}/${COOK_WEB_IMAGE_NAME}:${LMZJ_IMAGE_TAG}"

echo "==> Deploying lmzj-ai-shifu @ ${LMZJ_IMAGE_TAG}"
echo "    API:      ${API_IMAGE}"
echo "    Cook web: ${COOK_WEB_IMAGE}"

cd "${LMZJ_DEPLOY_PATH}"

echo "==> Pulling immutable images (no build on server)"
docker pull "${API_IMAGE}"
docker pull "${COOK_WEB_IMAGE}"

echo "==> Recreating stack with pulled images"
export LMZJ_API_IMAGE="${API_IMAGE}"
export LMZJ_COOK_WEB_IMAGE="${COOK_WEB_IMAGE}"
docker compose -f docker-compose.prod.yml up -d --no-build

echo "==> Project-scoped cleanup (keep current tag, never touch volumes)"
# Only prune dangling images for this project's repositories. Never run
# `docker system prune` or remove volumes or other projects' images.
docker image prune -f --filter "label=ai-shifu.project=lmzj-ai-shifu" || true

echo "==> Deployed ${LMZJ_IMAGE_TAG}. Rollback by re-running with the previous full SHA."
