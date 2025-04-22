from googleapiclient.discovery import build
from django.conf import settings

def get_youtube_service():
    """Create a YouTube API service object using the API key from settings."""
    return build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

def extract_channel_id_from_url(url):
    import re
    youtube = get_youtube_service()

    # 1. Channel ID (direct)
    match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)

    # 2. Handle like @channelname
    match = re.search(r"youtube\.com/@([a-zA-Z0-9_-]+)", url)
    if match:
        handle = match.group(1)
        res = youtube.search().list(q=handle, type='channel', part='id', maxResults=1).execute()
        return res['items'][0]['id']['channelId'] if res['items'] else None

    # 3. Legacy username (youtube.com/user/...)
    match = re.search(r"youtube\.com/user/([a-zA-Z0-9_-]+)", url)
    if match:
        username = match.group(1)
        res = youtube.channels().list(part='id', forUsername=username).execute()
        return res['items'][0]['id'] if res['items'] else None

    return None

def get_channel_details(channel_id):
    youtube = get_youtube_service()
    res = youtube.channels().list(
        part='snippet,statistics,contentDetails',
        id=channel_id
    ).execute()
    return res['items'][0] if res['items'] else None

def get_all_video_ids(channel_id):
    youtube = get_youtube_service()

    # Get uploads playlist ID
    uploads_playlist_id = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    video_ids = []
    next_page_token = None

    while True:
        res = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        video_ids += [item['contentDetails']['videoId'] for item in res['items']]
        next_page_token = res.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def get_video_details(video_ids):
    youtube = get_youtube_service()
    videos = []

    for i in range(0, len(video_ids), 50):  # API limit = 50
        chunk = video_ids[i:i + 50]
        res = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(chunk)
        ).execute()

        for item in res['items']:
            videos.append({
                'title': item['snippet']['title'],
                'link': f"https://www.youtube.com/watch?v={item['id']}",
                'duration': item['contentDetails']['duration'],
                'views': item['statistics'].get('viewCount'),
                'likes': item['statistics'].get('likeCount'),
                'comments': item['statistics'].get('commentCount'),
                'upload_date': item['snippet']['publishedAt'][:10]  # yyyy-mm-dd
            })

    return videos