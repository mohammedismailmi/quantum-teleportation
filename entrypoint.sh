#!/bin/sh
set -e

# Preload libgomp to prevent glibc "cannot allocate memory in static TLS block" error
GOMP_LIB=$(find /usr/lib -name "libgomp.so.1" 2>/dev/null | head -n 1)
if [ -z "$GOMP_LIB" ]; then
    GOMP_LIB=$(find /usr -name "libgomp*.so*" 2>/dev/null | head -n 1)
fi

if [ -n "$GOMP_LIB" ]; then
    echo "Preloading OpenMP library: $GOMP_LIB"
    export LD_PRELOAD="$GOMP_LIB:$LD_PRELOAD"
fi

PORT="${PORT:-8000}"
echo "Starting Uvicorn server on port $PORT..."
exec uvicorn server:app --host 0.0.0.0 --port "$PORT"
