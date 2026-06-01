import json
import urllib.request
import urllib.error

# Gemini 3.1 Flash Image on Fal.ai
MODEL_ENDPOINT = "https://fal.run/fal-ai/nano-banana-2/edit"
SCENE_PRESERVATION_SYSTEM_PROMPT = (
    "You are an image editing model for Blender renders. Use the provided input "
    "image as the strict source scene. Preserve the original camera angle, "
    "composition, object placement, geometry, proportions, perspective, lighting "
    "direction, and background unless the user explicitly asks to change them. "
    "Only apply the requested edit."
)
SUPPORTED_ASPECT_RATIOS = {
    "21:9", "16:9", "3:2", "4:3", "5:4", "1:1",
    "4:5", "3:4", "2:3", "9:16", "4:1", "1:4", "8:1", "1:8"
}

def get_aspect_ratio(width, height):
    """
    Converts Blender render dimensions to the nearest Fal.ai aspect ratio enum.
    """
    import math

    divisor = math.gcd(width, height)
    ratio = f"{width // divisor}:{height // divisor}"
    return ratio if ratio in SUPPORTED_ASPECT_RATIOS else "auto"

def get_resolution(width, height):
    """
    Maps Blender render dimensions to the model's resolution enum.
    """
    longest_side = max(width, height)
    if longest_side >= 3840:
        return "4K"
    if longest_side >= 2048:
        return "2K"
    if longest_side <= 512:
        return "0.5K"
    return "1K"

def build_scene_preserving_prompt(prompt):
    """
    Wraps the user prompt with explicit edit constraints to avoid scene drift.
    """
    return (
        "Edit the provided Blender render without changing the base scene. "
        "Keep the same camera, layout, object positions, scale, perspective, "
        "background, and overall composition. "
        f"User edit request: {prompt}"
    )

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
    Sends a request to Gemini 3.1 Flash Image on Fal.ai.
    """
    if not api_key:
        raise ValueError("API Key is missing")

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": build_scene_preserving_prompt(prompt),
        "num_images": 1,
        "aspect_ratio": get_aspect_ratio(width, height),
        "output_format": "png",
        "safety_tolerance": "4",
        "system_prompt": SCENE_PRESERVATION_SYSTEM_PROMPT,
        "resolution": get_resolution(width, height),
        "limit_generations": True,
    }
    
    endpoint = MODEL_ENDPOINT

    if image_url:
        payload["image_urls"] = [image_url]
        payload["sync_mode"] = True
    
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
        if url.startswith("data:"):
            import base64

            _, encoded_data = url.split(",", 1)
            with open(save_path, 'wb') as out_file:
                out_file.write(base64.b64decode(encoded_data))
            print(f"Saved to {save_path}")
            return

        with urllib.request.urlopen(url, timeout=60) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Saved to {save_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to download image: {e}")
