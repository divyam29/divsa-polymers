#!/bin/bash
# Convert JPG images to WebP format for better compression
# Requires: cwebp tool (from libwebp)
# Install: sudo apt-get install webp (Linux) or brew install webp (macOS)

ASSETS_DIR="static/assets"

if [ ! -d "$ASSETS_DIR" ]; then
    echo "Assets directory not found: $ASSETS_DIR"
    exit 1
fi

echo "Converting images to WebP format..."

for img in "$ASSETS_DIR"/*.{jpg,jpeg,png}; do
    [ -e "$img" ] || continue
    
    filename=$(basename "$img")
    filename_no_ext="${filename%.*}"
    output="$ASSETS_DIR/${filename_no_ext}.webp"
    
    if [ -f "$output" ]; then
        echo "Skipping $filename (WebP already exists)"
    else
        echo "Converting $filename to WebP..."
        cwebp -q 80 "$img" -o "$output"
        
        if [ $? -eq 0 ]; then
            original_size=$(du -h "$img" | cut -f1)
            webp_size=$(du -h "$output" | cut -f1)
            echo "  ✓ Created: $output (Original: $original_size, WebP: $webp_size)"
        else
            echo "  ✗ Failed to convert $filename"
        fi
    fi
done

echo "Done!"
