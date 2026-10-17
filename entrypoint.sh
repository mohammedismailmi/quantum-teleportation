#!/bin/bash
set -e

# Find the exact qiskit_aer bundled libgomp (critical for Qiskit Aer C++ engine)
AER_GOMP=$(find /usr/local/lib -path "*/qiskit_aer.libs/libgomp*.so*" 2>/dev/null | head -n 1)
if [ -z "$AER_GOMP" ]; then
    AER_GOMP=$(find /usr/local/lib -name "libgomp*.so*" 2>/dev/null | head -n 1)
fi

# Also find system libgomp
SYS_GOMP=$(find /usr/lib -name "libgomp.so.1" 2>/dev/null | head -n 1)

PRELOAD=""
if [ -n "$AER_GOMP" ]; then
    echo "Found Qiskit Aer bundled libgomp: $AER_GOMP"
    PRELOAD="$AER_GOMP"
fi

if [ -n "$SYS_GOMP" ]; then
    echo "Found System libgomp: $SYS_GOMP"
    if [ -n "$PRELOAD" ]; then
        PRELOAD="$PRELOAD:$SYS_GOMP"
    else
        PRELOAD="$SYS_GOMP"
    fi
fi

if [ -n "$PRELOAD" ]; then
    echo "Exporting LD_PRELOAD=$PRELOAD"
    export LD_PRELOAD="$PRELOAD"
fi

PORT="${PORT:-8000}"
echo "Starting Uvicorn on port $PORT..."
exec uvicorn server:app --host 0.0.0.0 --port "$PORT"
