#!/usr/bin/env python3
"""
Generate a smooth, lightweight animated showcase GIF for Aegis AI
cycling through key interface workflows:
1. Dashboard Login
2. Underwriter Workbench & Portfolio Triage
3. Individual SHAP Waterfall & Attribution
4. Corporate HR Portal & Department Comparison
5. Actuarial Pricing Engine & Risk Zones
"""

from pathlib import Path
from PIL import Image

def main():
    image_paths = [
        "docs/images/dashboard-login.png",
        "docs/images/underwriter-workbench.png",
        "docs/images/hr-wellness-portal.png",
        "docs/images/actuarial-pricing-model.png",
    ]
    
    target_w, target_h = 1000, 625
    frames = []
    
    # Load and normalize all images to target size with dark background
    loaded = []
    for p in image_paths:
        if not Path(p).is_file():
            continue
        im = Image.open(p).convert("RGBA")
        # Resize to fit within target
        im.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
        # Create canvas
        bg = Image.new("RGBA", (target_w, target_h), (13, 17, 23, 255))
        # Center image
        ox = (target_w - im.width) // 2
        oy = (target_h - im.height) // 2
        bg.paste(im, (ox, oy), im)
        loaded.append(bg)

    if not loaded:
        print("No images found to generate GIF")
        return

    # Create sequence with smooth cross-fade transitions
    durations = []
    num_slides = len(loaded)
    
    for i in range(num_slides):
        current_img = loaded[i]
        next_img = loaded[(i + 1) % num_slides]
        
        # Hold frame for 2.2 seconds (represented by a static hold or few frames)
        for _ in range(8):
            frames.append(current_img.convert("RGB"))
            durations.append(250) # 8 * 250 = 2000ms hold
            
        # 4 transition frames (fade)
        for step in range(1, 5):
            alpha = step / 5.0
            blended = Image.blend(current_img, next_img, alpha)
            frames.append(blended.convert("RGB"))
            durations.append(70) # smooth quick fade

    out_gif = "docs/images/aegis-showcase.gif"
    # Quantize palette for compact size
    frames[0].save(
        out_gif,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True
    )
    print(f"Saved animated showcase GIF to {out_gif}")

if __name__ == "__main__":
    main()
