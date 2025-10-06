"""
Icon Generator for DALS
Converts the PNG logo to various icon formats needed for favicon and Windows folder icon
"""

from PIL import Image
import os

def create_icons():
    # Define paths
    base_path = r"c:\Users\bryan\OneDrive\Desktop\Digital Assets Logistics Systems"
    logo_path = os.path.join(base_path, "DigitalAssetLogisticsSystem.png")
    icons_dir = os.path.join(base_path, "iss_module", "static", "icons")
    
    # Create icons directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    try:
        # Open the original logo
        original = Image.open(logo_path)
        print(f"✅ Loaded logo: {original.size}")
        
        # Convert to RGBA if not already
        if original.mode != 'RGBA':
            original = original.convert('RGBA')
        
        # Create various favicon sizes
        sizes = [16, 32, 48, 64, 96, 128, 256]
        
        for size in sizes:
            # Resize image
            resized = original.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG
            png_path = os.path.join(icons_dir, f"favicon-{size}x{size}.png")
            resized.save(png_path, "PNG")
            print(f"✅ Created: favicon-{size}x{size}.png")
        
        # Create ICO file (for Windows favicon)
        ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        ico_images = []
        
        for size in ico_sizes:
            resized = original.resize(size, Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        ico_path = os.path.join(icons_dir, "favicon.ico")
        ico_images[0].save(ico_path, "ICO", sizes=ico_sizes)
        print(f"✅ Created: favicon.ico")
        
        # Create Apple Touch Icon (180x180)
        apple_icon = original.resize((180, 180), Image.Resampling.LANCZOS)
        apple_path = os.path.join(icons_dir, "apple-touch-icon.png")
        apple_icon.save(apple_path, "PNG")
        print(f"✅ Created: apple-touch-icon.png")
        
        # Create Windows folder icon (256x256)
        folder_icon = original.resize((256, 256), Image.Resampling.LANCZOS)
        folder_path = os.path.join(base_path, "DALS-folder-icon.png")
        folder_icon.save(folder_path, "PNG")
        print(f"✅ Created: DALS-folder-icon.png")
        
        # Create large logo for potential use
        large_logo = original.resize((512, 512), Image.Resampling.LANCZOS)
        large_path = os.path.join(icons_dir, "logo-512.png")
        large_logo.save(large_path, "PNG")
        print(f"✅ Created: logo-512.png")
        
        print("\n🎉 All icons created successfully!")
        print(f"📁 Icons saved to: {icons_dir}")
        print(f"📁 Folder icon saved to: {folder_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DALS Icon Generator")
    print("=" * 50)
    
    # Check if PIL is available
    try:
        from PIL import Image
        print("✅ PIL/Pillow is available")
    except ImportError:
        print("❌ PIL/Pillow not found. Installing...")
        os.system("pip install Pillow")
        from PIL import Image
        print("✅ PIL/Pillow installed successfully")
    
    # Create icons
    success = create_icons()
    
    if success:
        print("\n📋 Manual Steps for Windows Folder Icon:")
        print("1. Right-click on the DALS folder")
        print("2. Select 'Properties'")
        print("3. Go to 'Customize' tab")
        print("4. Click 'Change Icon...'")
        print("5. Click 'Browse...' and select 'DALS-folder-icon.png'")
        print("6. Click 'OK' to apply")
    else:
        print("\n❌ Icon creation failed. Please check the logo file path.")