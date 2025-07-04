from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import re
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging

# Add the parent directory to the path to import instaloader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from instaloader import Instaloader, Profile, Post, Story, Hashtag
    from instaloader.exceptions import *
except ImportError as e:
    print(f"Failed to import instaloader: {e}")
    sys.exit(1)

app = FastAPI(title="Instagram Downloader API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLRequest(BaseModel):
    url: str

class ContentResponse(BaseModel):
    content_type: str
    title: str
    description: str
    thumbnail_url: str
    username: str
    download_options: Dict[str, Any]

class DownloadRequest(BaseModel):
    url: str
    download_type: str  # 'image', 'video', 'profile_pic', etc.

# Global Instaloader instance
loader = Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=True,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    quiet=True
)

def extract_shortcode_or_username(url: str) -> Tuple[str, str]:
    """Extract shortcode or username from Instagram URL and determine type."""
    
    # Clean URL
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Post/Reel patterns
    post_pattern = r'https://(?:www\.)?instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)'
    post_match = re.search(post_pattern, url)
    if post_match:
        return post_match.group(1), 'post'
    
    # Profile pattern
    profile_pattern = r'https://(?:www\.)?instagram\.com/([A-Za-z0-9_.]+)/?(?:\?.*)?$'
    profile_match = re.search(profile_pattern, url)
    if profile_match:
        return profile_match.group(1), 'profile'
    
    # Story pattern
    story_pattern = r'https://(?:www\.)?instagram\.com/stories/([A-Za-z0-9_.]+)'
    story_match = re.search(story_pattern, url)
    if story_match:
        return story_match.group(1), 'story'
    
    raise ValueError("Invalid Instagram URL format")

@app.post("/api/analyze", response_model=ContentResponse)
async def analyze_url(request: URLRequest):
    """Analyze Instagram URL and return content information."""
    try:
        shortcode_or_username, content_type = extract_shortcode_or_username(request.url)
        
        if content_type == 'post':
            # Handle post/reel
            try:
                post = Post.from_shortcode(loader.context, shortcode_or_username)
                
                download_options = {}
                if post.is_video:
                    download_options['video'] = {
                        'available': True,
                        'description': 'Download video file'
                    }
                if not post.is_video or loader.download_video_thumbnails:
                    download_options['image'] = {
                        'available': True,
                        'description': 'Download image/thumbnail'
                    }
                
                return ContentResponse(
                    content_type='reel' if post.is_video else 'post',
                    title=f"{'Reel' if post.is_video else 'Post'} by @{post.owner_username}",
                    description=post.caption[:100] + "..." if post.caption and len(post.caption) > 100 else post.caption or "",
                    thumbnail_url=post.url,
                    username=post.owner_username,
                    download_options=download_options
                )
            except Exception as e:
                logger.error(f"Error fetching post: {e}")
                raise HTTPException(status_code=400, detail=f"Could not fetch post: {str(e)}")
        
        elif content_type == 'profile':
            # Handle profile
            try:
                profile = Profile.from_username(loader.context, shortcode_or_username)
                
                download_options = {
                    'profile_pic': {
                        'available': True,
                        'description': 'Download profile picture'
                    }
                }
                
                return ContentResponse(
                    content_type='profile',
                    title=f"Profile: @{profile.username}",
                    description=profile.biography[:100] + "..." if profile.biography and len(profile.biography) > 100 else profile.biography or "",
                    thumbnail_url=profile.profile_pic_url,
                    username=profile.username,
                    download_options=download_options
                )
            except Exception as e:
                logger.error(f"Error fetching profile: {e}")
                raise HTTPException(status_code=400, detail=f"Could not fetch profile: {str(e)}")
        
        elif content_type == 'story':
            # Handle story (note: requires login for most stories)
            return ContentResponse(
                content_type='story',
                title=f"Story by @{shortcode_or_username}",
                description="Stories require Instagram login to access",
                thumbnail_url="",
                username=shortcode_or_username,
                download_options={
                    'story': {
                        'available': False,
                        'description': 'Stories require login (not supported in public mode)'
                    }
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported content type")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/download")
async def download_content(request: DownloadRequest):
    """Download Instagram content."""
    try:
        shortcode_or_username, content_type = extract_shortcode_or_username(request.url)
        
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            if content_type == 'post':
                post = Post.from_shortcode(loader.context, shortcode_or_username)
                
                if request.download_type == 'video' and post.is_video:
                    # Download video
                    video_url = post.video_url
                    if video_url:
                        response = loader.context.get_raw(video_url)
                        filename = f"{post.shortcode}.mp4"
                        file_path = temp_path / filename
                        
                        with open(file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        return Response(
                            content=content,
                            media_type="video/mp4",
                            headers={"Content-Disposition": f"attachment; filename={filename}"}
                        )
                    else:
                        raise HTTPException(status_code=400, detail="Video URL not available")
                
                elif request.download_type == 'image':
                    # Download image/thumbnail
                    image_url = post.url
                    response = loader.context.get_raw(image_url)
                    filename = f"{post.shortcode}.jpg"
                    file_path = temp_path / filename
                    
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    return Response(
                        content=content,
                        media_type="image/jpeg",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
            
            elif content_type == 'profile' and request.download_type == 'profile_pic':
                profile = Profile.from_username(loader.context, shortcode_or_username)
                
                # Download profile picture
                profile_pic_url = profile.profile_pic_url
                response = loader.context.get_raw(profile_pic_url)
                filename = f"{profile.username}_profile_pic.jpg"
                file_path = temp_path / filename
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                return Response(
                    content=content,
                    media_type="image/jpeg",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            
            else:
                raise HTTPException(status_code=400, detail="Invalid download type for this content")
                
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Instagram Downloader API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)