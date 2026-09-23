import os
import re
import html
import requests
import urllib.request
from typing import Optional, Dict, Any
import instaloader

class ContentExtractor:
    """Downloads actual images/media and captions from Instagram for Gemini Vision analysis."""
    
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False
        )
        self.headers = {
            'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
        }

    def extract_shortcode(self, url: str) -> Optional[str]:
        match = re.search(r'/(?:p|reel)/([A-Za-z0-9_-]+)', url)
        return match.group(1) if match else None

    def extract_from_url(self, url: str) -> Dict[str, Any]:
        clean_url = url.split("?")[0]
        shortcode = self.extract_shortcode(clean_url)
        
        caption = ""
        image_paths = []
        
        # 1. Download ACTUAL images using Instaloader (Real Visual Ingestion)
        if shortcode:
            try:
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                caption = post.caption or ""
                
                if post.typename == 'GraphSidecar':
                    for idx, node in enumerate(post.get_sidecar_nodes()):
                        img_path = os.path.join(self.download_dir, f"{shortcode}_slide_{idx+1}.jpg")
                        urllib.request.urlretrieve(node.display_url, img_path)
                        image_paths.append(img_path)
                elif post.typename in ['GraphImage', 'GraphVideo']:
                    img_path = os.path.join(self.download_dir, f"{shortcode}.jpg")
                    urllib.request.urlretrieve(post.url, img_path)
                    image_paths.append(img_path)
            except Exception as e:
                print(f"[Extractor Warning] Instaloader fetch: {e}")

        # 2. Fallback to OpenGraph metadata if Instaloader is rate limited
        if not caption:
            try:
                resp = requests.get(clean_url, headers=self.headers, timeout=12)
                if resp.status_code == 200:
                    desc_match = re.search(r'property="og:description"\s+content="([^"]+)"', resp.text)
                    if desc_match:
                        raw_desc = desc_match.group(1)
                        clean_desc = html.unescape(raw_desc)
                        if ' : "' in clean_desc:
                            caption = clean_desc.split(' : "', 1)[1].rstrip('". ')
                        else:
                            caption = clean_desc
                            
                    # Download og:image if no images yet
                    if not image_paths:
                        img_match = re.search(r'property="og:image"\s+content="([^"]+)"', resp.text)
                        if img_match:
                            og_img_url = html.unescape(img_match.group(1))
                            img_path = os.path.join(self.download_dir, f"og_image_{shortcode or 'temp'}.jpg")
                            urllib.request.urlretrieve(og_img_url, img_path)
                            image_paths.append(img_path)
            except Exception as e:
                print(f"[Extractor Warning] OG fetch: {e}")

        return {
            'success': bool(caption or image_paths),
            'caption': caption,
            'image_paths': image_paths,
            'primary_image': image_paths[0] if image_paths else None,
            'url': clean_url,
            'shortcode': shortcode
        }
