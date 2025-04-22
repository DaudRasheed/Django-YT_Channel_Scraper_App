from django.shortcuts import render
from django.http import HttpResponse
from .youtube_api import extract_channel_id_from_url, get_channel_details, get_all_video_ids, get_video_details
import openpyxl

def scrape_channel(request):
    data = {}

    if request.method == 'POST':
        url = request.POST.get('channel_url')

        try:
            channel_id = extract_channel_id_from_url(url)
            channel_info = get_channel_details(channel_id)
            video_ids = get_all_video_ids(channel_id)
            videos = get_video_details(video_ids)

            # Store video data in session for Excel download
            request.session['video_data'] = videos

            data = {
                'channel_title': channel_info['snippet']['title'],
                'total_videos': len(videos),
                'videos': videos
            }

        except Exception as e:
            data['error'] = str(e)

    return render(request, 'scraper/scrape.html', {'data': data})


def download_excel(request):
    videos = request.session.get('video_data', [])

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "YouTube Videos"

    # Add headers
    headers = ['Title', 'Link', 'Duration', 'Views', 'Likes', 'Comments', 'Upload Date']
    sheet.append(headers)

    # Add video data
    for video in videos:
        sheet.append([
            video.get('title'),
            video.get('link'),
            video.get('duration'),
            video.get('views'),
            video.get('likes'),
            video.get('comments'),
            video.get('upload_date')
        ])

    # Prepare and return the Excel file as a response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=video_data.xlsx'
    workbook.save(response)
    return response
