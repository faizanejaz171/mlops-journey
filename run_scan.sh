#!/bin/bash
# run_scan.sh — automated image scan with timestamped output

FOLDER="${IMAGE_FOLDER:-./test_images}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT="reports/scan_${TIMESTAMP}.csv"

mkdir -p reports

echo "Starting scan of: $FOLDER"
python day2.py --input "$FOLDER" --output "$OUTPUT"
echo "Done. Report saved to: $OUTPUT"
