import json
import urllib.request
import urllib.error
import time
import ssl

# Default to Google Nano Banana Pro on Fal.ai
MODEL_ENDPOINT = "https://fal.run/google/nano-banana-pro"

def encode_image_to_base64(image_path):
    """
    Encodes an image file to a base64 data URI string.
    """
    import base64
    import mimetypes
    
    mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    return f"data:{mime_type};base64,{encoded_string}"

def send_api_request(api_key, prompt, image_url=None, strength=0.75, width=1920, height=1080):
    """
    Sends a request to Fal.ai. If image_url is provided, performs Image-to-Image.
    """
    if not api_key:
        raise ValueError("API Key is missing")

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    # API Payload
    payload = {
        "prompt": prompt,
        "image_size": {
            "width": width,
            "height": height
        },
        "num_inference_steps": 30
    }
    
    endpoint = MODEL_ENDPOINT

    # Add Image-to-Image parameters if an image is provided
    if image_url:
        # Switch to the Edit endpoint
        endpoint = "https://fal.run/fal-ai/nano-banana/edit" 
        # The edit endpoint expects 'image_urls' for the base image
        payload["image_urls"] = [image_url]
        payload["sync_mode"] = True # Recommended for edit endpoint
        print(f"Switching to Edit Endpoint: {endpoint}")
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(endpoint, data=data, headers=headers, method='POST')

    print(f"Sending request to {endpoint}...")
    
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                print("API Response:", result)
                return parse_result(result)
            else:
                raise RuntimeError(f"API Error: {response.status} - {response.reason}")
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"HTTP Error {e.code}: {error_body}")
        raise RuntimeError(f"Fal.ai Error: {e.code}")
    except Exception as e:
        print(f"Network Error: {e}")
        raise e

def parse_result(result):
    """
    Extracts the image URL from the Fal.ai response.
    """
    # Check if result is directly an image object or list
    if "images" in result and len(result["images"]) > 0:
        return result["images"][0]["url"]
    
    # Handle queued or other formats if needed (Nano Banana usually returns fast)
    if "image" in result: # Some endpoints
        return result["image"]["url"]
        
    raise RuntimeError("No image found in API response")

def download_image(url, save_path):
    """
    Downloads the image from URL to the save_path.
    """
    print(f"Downloading image from {url}...")
    try:
        with urllib.request.urlopen(url, timeout=60) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved to {save_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to download image: {e}")
