#!/bin/sh

# =================================================================
# Log Rotation Script for Teder Trading Bot
# =================================================================

set -e

LOG_DIR="/logs"
MAX_SIZE="10M"
MAX_FILES=7
COMPRESS=true

# Function to rotate a single log file
rotate_log() {
    local logfile="$1"
    local basename="${logfile%.*}"
    local extension="${logfile##*.}"
    
    if [ ! -f "$LOG_DIR/$logfile" ]; then
        return
    fi
    
    # Check file size
    size=$(du -k "$LOG_DIR/$logfile" | cut -f1)
    max_size_kb=10240  # 10MB in KB
    
    if [ "$size" -gt "$max_size_kb" ]; then
        echo "Rotating $logfile (size: ${size}KB)"
        
        # Rotate existing logs
        for i in $(seq $((MAX_FILES-1)) -1 1); do
            if [ -f "$LOG_DIR/${basename}.${i}.${extension}" ]; then
                if [ $i -eq $((MAX_FILES-1)) ]; then
                    rm -f "$LOG_DIR/${basename}.${i}.${extension}"
                    rm -f "$LOG_DIR/${basename}.${i}.${extension}.gz"
                else
                    mv "$LOG_DIR/${basename}.${i}.${extension}" "$LOG_DIR/${basename}.$((i+1)).${extension}"
                    if [ -f "$LOG_DIR/${basename}.${i}.${extension}.gz" ]; then
                        mv "$LOG_DIR/${basename}.${i}.${extension}.gz" "$LOG_DIR/${basename}.$((i+1)).${extension}.gz"
                    fi
                fi
            fi
        done
        
        # Move current log to .1
        mv "$LOG_DIR/$logfile" "$LOG_DIR/${basename}.1.${extension}"
        
        # Create new empty log file
        touch "$LOG_DIR/$logfile"
        chmod 644 "$LOG_DIR/$logfile"
        
        # Compress rotated log if enabled
        if [ "$COMPRESS" = true ]; then
            gzip "$LOG_DIR/${basename}.1.${extension}"
        fi
        
        echo "Log rotation completed for $logfile"
    fi
}

# Main execution
echo "Starting log rotation at $(date)"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Rotate common log files
if [ -f "$LOG_DIR/live_trading.log" ]; then
    rotate_log "live_trading.log"
fi

if [ -f "$LOG_DIR/error.log" ]; then
    rotate_log "error.log"
fi

if [ -f "$LOG_DIR/access.log" ]; then
    rotate_log "access.log"
fi

if [ -f "$LOG_DIR/debug.log" ]; then
    rotate_log "debug.log"
fi

# Rotate any other .log files
for logfile in "$LOG_DIR"/*.log; do
    if [ -f "$logfile" ]; then
        filename=$(basename "$logfile")
        case "$filename" in
            "live_trading.log"|"error.log"|"access.log"|"debug.log")
                # Already processed above
                ;;
            *)
                rotate_log "$filename"
                ;;
        esac
    fi
done

# Clean up old compressed logs beyond retention period
find "$LOG_DIR" -name "*.log.gz" -mtime +30 -delete 2>/dev/null || true

echo "Log rotation completed at $(date)"