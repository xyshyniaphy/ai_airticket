#!/usr/bin/env python3
"""
Test script for Chrome headless rendering functionality in Docker
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_chrome_rendering():
    """Test if Chrome headless rendering works in the Docker environment."""
    print("🧪 Testing Chrome headless rendering...")
    
    # Create a simple HTML test page
    test_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Page</title>
    <style>
        body { 
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            margin: 0; 
            padding: 20px; 
            color: white;
            text-align: center;
        }
        .container {
            max-width: 390px;
            margin: 0 auto;
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 { font-size: 2em; margin-bottom: 15px; }
        p { font-size: 1.2em; line-height: 1.6; }
        .emoji { font-size: 3em; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">🛫</div>
        <h1>航班报告测试</h1>
        <p>这是Chrome无头渲染测试页面</p>
        <p>如果看到此PNG，说明Chrome渲染功能正常！</p>
        <div class="emoji">📱</div>
    </div>
</body>
</html>"""
    
    # Save test HTML
    html_path = "/tmp/test_render.html"
    png_path = "/tmp/test_render.png"
    
    try:
        os.makedirs("/tmp", exist_ok=True)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(test_html)
        
        print(f"Test HTML saved to: {html_path}")
        
        # Set up Chrome options for Docker environment
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # Mobile optimization
        chrome_options.add_argument("--window-size=390,844")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1")
        
        print("Launching Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get absolute path and convert to file URL
        abs_html_path = os.path.abspath(html_path)
        file_url = f"file://{abs_html_path}"
        
        print(f"Loading HTML file: {file_url}")
        driver.get(file_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get full page height
        total_height = driver.execute_script("return document.body.scrollHeight")
        print(f"Page height: {total_height}px")
        
        # Set window size for full page screenshot
        driver.set_window_size(390, total_height + 100)
        
        # Take screenshot
        print(f"Taking screenshot and saving to: {png_path}")
        driver.save_screenshot(png_path)
        
        # Cleanup
        driver.quit()
        
        # Check if PNG was created
        if os.path.exists(png_path):
            file_size = os.path.getsize(png_path)
            print(f"✅ PNG screenshot created successfully!")
            print(f"📊 File size: {file_size} bytes")
            print(f"📁 Location: {png_path}")
            return True
        else:
            print("❌ PNG screenshot was not created")
            return False
            
    except Exception as e:
        print(f"❌ Chrome rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chrome_rendering()
    if success:
        print("\n🎉 Chrome headless rendering test completed successfully!")
    else:
        print("\n💥 Chrome headless rendering test failed!")
        exit(1)