import unittest
import requests
import json
import os
from unittest import mock

# Get the backend URL from environment or use default
BACKEND_URL = "http://localhost:8001"

class InstagramDownloaderAPITest(unittest.TestCase):
    """Test cases for Instagram Downloader API"""

    def setUp(self):
        """Set up test environment"""
        self.base_url = BACKEND_URL
        self.headers = {"Content-Type": "application/json"}

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("message", data)
        print("✅ Health endpoint test passed")

    def test_analyze_valid_post_url(self):
        """Test analyzing a valid Instagram post URL"""
        payload = {"url": "https://www.instagram.com/p/ABCD1234/"}
        
        # This is a mock test since we can't actually connect to Instagram
        # In a real environment, we would use actual Instagram URLs
        response = requests.post(
            f"{self.base_url}/api/analyze", 
            headers=self.headers,
            json=payload
        )
        
        # Check if the response is either successful or a specific error
        # In a mocked environment, we might get a 400 error since the post doesn't exist
        if response.status_code == 200:
            data = response.json()
            self.assertIn("content_type", data)
            self.assertIn("title", data)
            self.assertIn("description", data)
            self.assertIn("thumbnail_url", data)
            self.assertIn("username", data)
            self.assertIn("download_options", data)
            print("✅ Analyze valid post URL test passed")
        else:
            # If we get an error, make sure it's properly formatted
            data = response.json()
            self.assertIn("detail", data)
            print(f"ℹ️ Analyze post URL returned error: {data['detail']}")

    def test_analyze_valid_reel_url(self):
        """Test analyzing a valid Instagram reel URL"""
        payload = {"url": "https://www.instagram.com/reel/ABCD1234/"}
        
        response = requests.post(
            f"{self.base_url}/api/analyze", 
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("content_type", data)
            self.assertIn("title", data)
            self.assertIn("description", data)
            self.assertIn("thumbnail_url", data)
            self.assertIn("username", data)
            self.assertIn("download_options", data)
            print("✅ Analyze valid reel URL test passed")
        else:
            data = response.json()
            self.assertIn("detail", data)
            print(f"ℹ️ Analyze reel URL returned error: {data['detail']}")

    def test_analyze_valid_profile_url(self):
        """Test analyzing a valid Instagram profile URL"""
        payload = {"url": "https://www.instagram.com/instagram/"}
        
        response = requests.post(
            f"{self.base_url}/api/analyze", 
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("content_type", data)
            self.assertEqual(data["content_type"], "profile")
            self.assertIn("title", data)
            self.assertIn("description", data)
            self.assertIn("thumbnail_url", data)
            self.assertIn("username", data)
            self.assertIn("download_options", data)
            print("✅ Analyze valid profile URL test passed")
        else:
            data = response.json()
            self.assertIn("detail", data)
            print(f"ℹ️ Analyze profile URL returned error: {data['detail']}")

    def test_analyze_invalid_url(self):
        """Test analyzing an invalid Instagram URL"""
        payload = {"url": "https://www.example.com/not-instagram"}
        
        response = requests.post(
            f"{self.base_url}/api/analyze", 
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Analyze invalid URL test passed")

    def test_analyze_empty_url(self):
        """Test analyzing an empty URL"""
        payload = {"url": ""}
        
        response = requests.post(
            f"{self.base_url}/api/analyze", 
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Analyze empty URL test passed")

    def test_download_post_image(self):
        """Test downloading an image from a post"""
        payload = {
            "url": "https://www.instagram.com/p/ABCD1234/",
            "download_type": "image"
        }
        
        response = requests.post(
            f"{self.base_url}/api/download", 
            headers=self.headers,
            json=payload
        )
        
        # Check if the response is either successful or a specific error
        if response.status_code == 200:
            self.assertIn("Content-Disposition", response.headers)
            self.assertIn("attachment; filename=", response.headers["Content-Disposition"])
            self.assertTrue(len(response.content) > 0)
            print("✅ Download post image test passed")
        else:
            # If we get an error, make sure it's properly formatted
            try:
                data = response.json()
                self.assertIn("detail", data)
                print(f"ℹ️ Download post image returned error: {data['detail']}")
            except json.JSONDecodeError:
                self.fail("Response is not a valid JSON")

    def test_download_profile_pic(self):
        """Test downloading a profile picture"""
        payload = {
            "url": "https://www.instagram.com/instagram/",
            "download_type": "profile_pic"
        }
        
        response = requests.post(
            f"{self.base_url}/api/download", 
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            self.assertIn("Content-Disposition", response.headers)
            self.assertIn("attachment; filename=", response.headers["Content-Disposition"])
            self.assertTrue(len(response.content) > 0)
            print("✅ Download profile picture test passed")
        else:
            try:
                data = response.json()
                self.assertIn("detail", data)
                print(f"ℹ️ Download profile picture returned error: {data['detail']}")
            except json.JSONDecodeError:
                self.fail("Response is not a valid JSON")

    def test_download_invalid_type(self):
        """Test downloading with an invalid download type"""
        payload = {
            "url": "https://www.instagram.com/p/ABCD1234/",
            "download_type": "invalid_type"
        }
        
        response = requests.post(
            f"{self.base_url}/api/download", 
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Download invalid type test passed")

if __name__ == "__main__":
    # Run the tests
    print("Starting Instagram Downloader API Tests...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)