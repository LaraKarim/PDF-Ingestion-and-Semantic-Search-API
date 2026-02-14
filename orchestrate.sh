
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  echo "Usage: $0 --action start | --action terminate"
  echo "  start     Build and start app + ChromaDB in detached mode."
  echo "  terminate Stop and remove containers, volumes, and networks."
  exit 1
}

action=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --action)
      action="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

if [[ -z "$action" ]]; then
  echo "Error: --action is required."
  usage
fi

case "$action" in
  start)
    echo "Building and starting services (detached)..."
    if ! docker compose up -d --build; then
      echo "Error: docker compose up failed." >&2
      exit 1
    fi
    echo ""
    echo "Started. Containers are running in the background (this script can exit)."
    echo "  API:      http://localhost:8000"
    echo "  ChromaDB:  http://localhost:8001"
    echo ""
    echo "Container status:"
    docker compose ps
    echo ""
    echo "To view logs: docker compose logs -f app"
    echo "To stop:      $0 --action terminate"
    echo ""
    read -p "Press Enter to return to the prompt (containers keep running)..."
    ;;
  terminate)
    echo "Stopping and removing containers, volumes, and networks..."
    if ! docker compose down -v; then
      echo "Error: docker compose down failed." >&2
      exit 1
    fi
    echo "Terminated."
    ;;
  *)
    echo "Error: unknown action '$action'."
    usage
    ;;
esac
