#!/usr/bin/env python3
"""
Convert JPG/PNG images to WebP format for better compression
Requires: Pillow (pip install Pillow)
Usage: python convert_to_webp.py
"""

import os
import sys
from pathlib import Path

# Toggle: Delete originals after successful conversion?
DELETE_ORIGINALS = False

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)


def convert_to_webp(image_path, output_path, quality=80):
    """Convert image to WebP format"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                rgb_img.save(output_path, 'WEBP', quality=quality, method=6)
            else:
                img.save(output_path, 'WEBP', quality=quality, method=6)
        return True
    except Exception as e:
        print(f"  ✗ Error converting {image_path}: {e}")
        return False


def delete_original(image_path):
    """Delete original image safely"""
    try:
        os.remove(image_path)
        print(f"   🗑️ Deleted original: {image_path.name}")
        return True
    except Exception as e:
        print(f"   ⚠️ Could not delete {image_path.name}: {e}")
        return False


def get_file_size(file_path):
    """Get file size in human-readable format"""
    size = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def main():
    """Main conversion function"""
    assets_dir = Path('static/assets')
    
    if not assets_dir.exists():
        print(f"Error: Assets directory not found: {assets_dir}")
        sys.exit(1)
    
    print("Converting images to WebP format...")
    converted = 0
    skipped = 0
    failed = 0
    
    image_extensions = ('.jpg', '.jpeg', '.png')
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(assets_dir.glob(f'*{ext}'))
        image_files.extend(assets_dir.glob(f'*{ext.upper()}'))
    
    if not image_files:
        print(f"No images found in {assets_dir}")
        return
    
    for image_path in sorted(set(image_files)):
        filename = image_path.name
        filename_no_ext = image_path.stem
        output_path = assets_dir / f'{filename_no_ext}.webp'
        
        if output_path.exists():
            print(f"⊘ Skipping {filename} (WebP already exists)")
            skipped += 1
        else:
            print(f"Converting {filename}...", end=" ")
            if convert_to_webp(image_path, output_path):
                original_size = get_file_size(image_path)
                webp_size = get_file_size(output_path)
                reduction = (1 - os.path.getsize(output_path) / os.path.getsize(image_path)) * 100
                print(f"✓ ({original_size} → {webp_size}, {reduction:.0f}% smaller)")
                
                if DELETE_ORIGINALS:
                    delete_original(image_path)

                converted += 1
            else:
                failed += 1
    
    print(f"\n✓ Done! Converted: {converted}, Skipped: {skipped}, Failed: {failed}")
    
    if converted > 0:
        print(f"\nWebP images created in: {assets_dir}")
        if DELETE_ORIGINALS:
            print("Original JPG/PNG files have been deleted after successful conversion.")
        else:
            print("Original JPG/PNG files were kept (deletion disabled).")


if __name__ == '__main__':
    main()
