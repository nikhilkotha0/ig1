import React, { useState } from 'react';
import axios from 'axios';
import { Download, Instagram, AlertCircle, CheckCircle, Loader2, Image, Video, User } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [contentData, setContentData] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const handleAnalyze = async () => {
    if (!url.trim()) {
      setError('Please enter a valid Instagram URL');
      return;
    }

    setLoading(true);
    setError('');
    setContentData(null);
    setDownloadSuccess(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
        url: url.trim()
      });
      
      setContentData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze URL. Please check if the URL is valid and the content is public.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (downloadType) => {
    setDownloading(true);
    setError('');
    setDownloadSuccess(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/download`, {
        url: url.trim(),
        download_type: downloadType
      }, {
        responseType: 'blob'
      });

      // Create blob URL and trigger download
      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'instagram_download';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setDownloadSuccess(true);
      setTimeout(() => setDownloadSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Download failed. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const getContentIcon = (contentType) => {
    switch (contentType) {
      case 'post':
        return <Image className="w-5 h-5" />;
      case 'reel':
        return <Video className="w-5 h-5" />;
      case 'profile':
        return <User className="w-5 h-5" />;
      default:
        return <Instagram className="w-5 h-5" />;
    }
  };

  const getDownloadIcon = (downloadType) => {
    switch (downloadType) {
      case 'video':
        return <Video className="w-4 h-4" />;
      case 'image':
        return <Image className="w-4 h-4" />;
      case 'profile_pic':
        return <User className="w-4 h-4" />;
      default:
        return <Download className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center items-center gap-3 mb-4">
            <Instagram className="w-10 h-10 text-instagram-500" />
            <h1 className="text-4xl font-bold text-gray-800">Instagram Downloader</h1>
          </div>
          <p className="text-gray-600 text-lg">
            Download Instagram posts, reels, stories, and profile pictures easily
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-2xl mx-auto">
          {/* URL Input */}
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="mb-4">
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                Instagram URL
              </label>
              <div className="flex gap-3">
                <input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste Instagram URL here (e.g., https://www.instagram.com/p/...)"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-instagram-500 focus:border-instagram-500 outline-none"
                  disabled={loading}
                />
                <button
                  onClick={handleAnalyze}
                  disabled={loading || !url.trim()}
                  className="px-6 py-3 bg-instagram-500 text-white rounded-lg hover:bg-instagram-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Analyze
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* Supported URLs Info */}
            <div className="text-sm text-gray-500">
              <p className="mb-1">Supported URLs:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Posts: https://www.instagram.com/p/...</li>
                <li>Reels: https://www.instagram.com/reel/...</li>
                <li>Profiles: https://www.instagram.com/username/</li>
                <li>Stories: https://www.instagram.com/stories/username/ (public only)</li>
              </ul>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          )}

          {/* Success Message */}
          {downloadSuccess && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <p className="text-green-700">Download completed successfully!</p>
              </div>
            </div>
          )}

          {/* Content Preview */}
          {contentData && (
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                {getContentIcon(contentData.content_type)}
                <h2 className="text-xl font-semibold text-gray-800">
                  {contentData.title}
                </h2>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Preview */}
                <div>
                  {contentData.thumbnail_url && (
                    <div className="mb-4">
                      <img
                        src={contentData.thumbnail_url}
                        alt="Content preview"
                        className="w-full h-48 object-cover rounded-lg border"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div className="text-sm text-gray-600">
                    <p className="font-medium mb-1">@{contentData.username}</p>
                    {contentData.description && (
                      <p className="text-gray-500">{contentData.description}</p>
                    )}
                  </div>
                </div>

                {/* Download Options */}
                <div>
                  <h3 className="font-medium text-gray-800 mb-3">Download Options</h3>
                  <div className="space-y-2">
                    {Object.entries(contentData.download_options).map(([key, option]) => (
                      <button
                        key={key}
                        onClick={() => handleDownload(key)}
                        disabled={!option.available || downloading}
                        className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                          option.available
                            ? 'border-instagram-200 hover:border-instagram-300 hover:bg-instagram-50 text-gray-700'
                            : 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        {downloading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          getDownloadIcon(key)
                        )}
                        <div className="flex-1 text-left">
                          <p className="font-medium capitalize">{key.replace('_', ' ')}</p>
                          <p className="text-sm text-gray-500">{option.description}</p>
                        </div>
                        {option.available && (
                          <Download className="w-4 h-4" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500 text-sm">
          <p>Made with ❤️ for Instagram content downloading</p>
          <p className="mt-1">This tool respects Instagram's terms of service and only downloads public content.</p>
        </div>
      </div>
    </div>
  );
}

export default App;