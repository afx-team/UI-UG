#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-afx-team/UI-UG2-4B}"
exec vllm serve "$MODEL_PATH" \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --served-model-name "${SERVED_MODEL_NAME:-uiug2}" \
  --dtype bfloat16 \
  --tensor-parallel-size "${TENSOR_PARALLEL_SIZE:-1}" \
  --max-model-len "${MAX_MODEL_LEN:-8192}" \
  "$@"
