#!/bin/bash

echo "Stopping existing car_price_app.py processes if running..."

# main_1.py işlemini durdur
MAIN_1_PID=$(ps aux | grep 'car_price_app.py' | grep -v grep | awk '{print $2}')

if [ -n "$MAIN_1_PID" ]; then
    echo "Stopping car_price_app.py (PID: $MAIN_1_PID)..."
    kill -9 $MAIN_1_PID
else
    echo "No running car_price_app.py process found."
fi

# Çalışma dizinini ayarla
cd /home/sabankara/personal_developing/car_price || exit


# car_price_app.py başlat
echo "Starting car_price_app.py on port 8220..."

nohup streamlit run /home/sabankara/personal_developing/car_price/car_price_app.py --server.port 8220 > /home/sabankara/personal_developing/car_price/logs/car_price_nohup.out 2>&1 &

echo "Processes started successfully!"


# Betiği çalıştırmadan önce çalıştırma izni verin:
# chmod +x run.sh