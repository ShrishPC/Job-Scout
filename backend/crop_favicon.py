import os
import sys
from PIL import Image, ImageChops

def crop_and_create_icon(src_path, dest_dir):
    if not os.path.exists(src_path):
        print(f"Source file {src_path} not found.")
        sys.exit(1)
        
    print(f"Loading image from {src_path}...")
    im = Image.open(src_path)
    
    # 1. Convert to RGBA to ensure alpha channel support
    im = im.convert("RGBA")
    
    # 2. Crop uniform borders (trim)
    # Get background color from the corner pixel (0,0)
    bg_color = im.getpixel((0, 0))
    print(f"Corner background color detected: {bg_color}")
    
    # If the corner is transparent, PIL's getbbox() will automatically crop transparent space
    if bg_color[3] == 0:
        print("Trimming transparent background...")
        bbox = im.getbbox()
    else:
        # Otherwise, trim solid color background
        print("Trimming solid color background...")
        bg = Image.new("RGBA", im.size, bg_color)
        diff = ImageChops.difference(im, bg)
        # Convert to grayscale and apply threshold to handle compression noise (e.g. 254 vs 255)
        diff_gray = diff.convert("L")
        diff_thresholded = diff_gray.point(lambda p: 255 if p > 15 else 0)
        bbox = diff_thresholded.getbbox()
        
    if bbox:
        print(f"Cropping image to bounding box: {bbox}")
        im = im.crop(bbox)
    else:
        print("No distinct border found. Using full image.")

    # 3. Make it a square (pad the smaller dimension to prevent stretching)
    width, height = im.size
    max_dim = max(width, height)
    print(f"Cropped dimensions: {width}x{height}. Creating {max_dim}x{max_dim} square...")
    
    square_im = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
    # Paste centered
    x_offset = (max_dim - width) // 2
    y_offset = (max_dim - height) // 2
    square_im.paste(im, (x_offset, y_offset))
    
    # 4. Resize and save
    os.makedirs(dest_dir, exist_ok=True)
    
    # Save as 512x512 png (Next.js automatically routes icon.png)
    icon_png_path = os.path.join(dest_dir, "icon.png")
    png_final = square_im.resize((512, 512), Image.Resampling.LANCZOS)
    png_final.save(icon_png_path, "PNG")
    print(f"Saved PNG icon to {icon_png_path}")
    
    # Save as ICO (standard fallback for older browsers)
    icon_ico_path = os.path.join(dest_dir, "favicon.ico")
    square_im.save(
        icon_ico_path, 
        format="ICO", 
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)]
    )
    print(f"Saved ICO favicon to {icon_ico_path}")
    
if __name__ == "__main__":
    src = "/home/rishav/Downloads/CV/JobScout.png"
    dest = "/home/rishav/job-scout/frontend/src/app"
    crop_and_create_icon(src, dest)
