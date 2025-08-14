import os
from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, Any, List

# API 密钥配置
API_KEY = "YOUR_API_KEY"

# MCP 服务器和 YouTube API 服务
mcp = FastMCP("youtube_sentiment_analyzer")
youtube = build('youtube', 'v3', developerKey=API_KEY)
analyzer = SentimentIntensityAnalyzer()


@mcp.tool()
def get_video_id_from_url(url: str) -> str:
    """
    Extracts the video ID from a YouTube video URL.

    Args:
        url: The YouTube video URL.

    Returns:
        The video ID as a string.
    """
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    else:
        return "Error: Invalid YouTube URL"


@mcp.tool()
def get_video_comments(video_id: str) -> List[str]:
    """
    Retrieves the first 50 comments of a YouTube video.

    Args:
        video_id: The ID of the YouTube video.

    Returns:
        A list of comment texts.
    """
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=50
        )
        response = request.execute()

        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        return comments

    except Exception as e:
        return [f"Error fetching comments: {str(e)}"]


@mcp.tool()
def analyze_comments_sentiment(video_url: str) -> Dict[str, Any]:
    """
    Analyzes the sentiment of comments for a given YouTube video URL.

    Args:
        video_url: The URL of the YouTube video.

    Returns:
        A dictionary containing the sentiment analysis results.
    """
    video_id = get_video_id_from_url(video_url)
    if "Error" in video_id:
        return {"error": video_id}

    comments = get_video_comments(video_id)
    if not comments or "Error" in comments[0]:
        return {"error": comments[0]}

    sentiment_scores = {
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'total': len(comments)
    }

    for comment in comments:
        score = analyzer.polarity_scores(comment)
        if score['compound'] >= 0.05:
            sentiment_scores['positive'] += 1
        elif score['compound'] <= -0.05:
            sentiment_scores['negative'] += 1
        else:
            sentiment_scores['neutral'] += 1

    return sentiment_scores


if __name__ == "__main__":
    print("Starting YouTube Sentiment MCP server. Waiting for Cursor to connect...")
    mcp.run(transport="stdio")
