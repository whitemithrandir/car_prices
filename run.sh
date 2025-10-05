#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/home/ubuntumithrandir/python_project/car_price"
VENV_DIR="/home/ubuntumithrandir/python_project/car_price/myenv"
PY="$VENV_DIR/bin/python"
APP="$APP_DIR/car_price_app.py"
LOG_DIR="$APP_DIR/logs"
PORT=8220

mkdir -p "$LOG_DIR"
cd "$APP_DIR"

# Streamlit'i tamamen headless ve promptsuz çalıştır
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo "Stopping existing $APP if running..."
pkill -f "$APP" || true

echo "Starting $APP on port $PORT..."
# stdin'i /dev/null'dan kapatıyoruz ki e-posta prompt'u asla beklemesin
nohup "$PY" -m streamlit run "$APP" \
  --server.port "$PORT" \
  --server.address 0.0.0.0 \
  --logger.level info \
  </dev/null > "$LOG_DIR/car_price_nohup.out" 2>&1 &

echo "Processes started successfully! PID: $!"


# #!/bin/bash

# echo "Stopping existing car_price_app.py processes if running..."

# # main_1.py işlemini durdur
# MAIN_1_PID=$(ps aux | grep 'car_price_app.py' | grep -v grep | awk '{print $2}')

# if [ -n "$MAIN_1_PID" ]; then
#     echo "Stopping car_price_app.py (PID: $MAIN_1_PID)..."
#     kill -9 $MAIN_1_PID
# else
#     echo "No running car_price_app.py process found."
# fi

# # Çalışma dizinini ayarla
# cd /home/ubuntumithrandir/python_project/car_price || exit


# # car_price_app.py başlat
# echo "Starting car_price_app.py on port 8220..."

# nohup streamlit run /home/ubuntumithrandir/python_project/car_price/car_price_app.py --server.port 8220 > /home/ubuntumithrandir/python_project/car_price/logs/car_price_nohup.out 2>&1 &

# echo "Processes started successfully!"


# # Betiği çalıştırmadan önce çalıştırma izni verin:
# # chmod +x run.sh
# # /home/ubuntumithrandir/python_project/car_price/run.sh
