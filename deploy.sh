#!/usr/bin/env bash
# deploy.sh — Déploiement Nexus-Diagnostix sur K8s depuis le serveur
# Usage : bash deploy.sh [--tag sha-abc1234]
# Les secrets sont stockés localement sur le serveur dans /root/.diagnostix/values-secret.yaml
set -euo pipefail

# ---------------------------------------------------------------------------
RELEASE="diagnostix"
NAMESPACE="diagnostix"
CHART_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/helm" && pwd)"
SECRETS_FILE="${DIAGNOSTIX_SECRETS:-/root/.diagnostix/values-secret.yaml}"
IMAGE_TAG="${1:-latest}"

# Extraire --tag si passé en argument nommé
if [[ "$IMAGE_TAG" == "--tag" ]]; then
  IMAGE_TAG="${2:-latest}"
fi

# ---------------------------------------------------------------------------
log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== Nexus-Diagnostix Deploy ==="
log "Release  : $RELEASE"
log "Namespace: $NAMESPACE"
log "Image tag: $IMAGE_TAG"
log "Secrets  : $SECRETS_FILE"

# Vérifications préalables
if [[ ! -f "$SECRETS_FILE" ]]; then
  echo ""
  echo "ERREUR : Fichier secrets introuvable : $SECRETS_FILE"
  echo ""
  echo "Créer le fichier à partir du modèle :"
  echo "  mkdir -p /root/.diagnostix"
  echo "  cp $(dirname "$CHART_DIR")/helm/values-secret.yaml.example $SECRETS_FILE"
  echo "  nano $SECRETS_FILE   # remplir toutes les valeurs"
  exit 1
fi

if ! command -v helm &>/dev/null; then
  echo "ERREUR : helm non installé. Installer avec :"
  echo "  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash"
  exit 1
fi

# Ajouter Bitnami si pas encore fait
if ! helm repo list 2>/dev/null | grep -q bitnami; then
  log "Ajout du repo Bitnami..."
  helm repo add bitnami https://charts.bitnami.com/bitnami
fi
helm repo update --fail-on-repo-update-failure bitnami 2>/dev/null || true

# Dépendances Helm
log "Mise à jour des dépendances Helm..."
helm dependency update "$CHART_DIR"

# Créer le namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Générer le secret GHCR pull (token PAT local ou image publique)
if [[ -n "${GHCR_TOKEN:-}" ]]; then
  log "Configuration du pull secret GHCR..."
  kubectl create secret docker-registry ghcr-secret \
    --docker-server=ghcr.io \
    --docker-username="${GHCR_USER:-couldevlop}" \
    --docker-password="$GHCR_TOKEN" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -
fi

# Déploiement Helm
log "Déploiement Helm..."
helm upgrade --install "$RELEASE" "$CHART_DIR" \
  --namespace "$NAMESPACE" \
  --values "$CHART_DIR/values.yaml" \
  --values "$CHART_DIR/values-production.yaml" \
  --values "$SECRETS_FILE" \
  --set image.backend.tag="$IMAGE_TAG" \
  --set image.frontend.tag="$IMAGE_TAG" \
  --wait \
  --timeout 15m \
  --atomic

log "=== Déploiement terminé ==="
echo ""
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get ingress -n "$NAMESPACE"
