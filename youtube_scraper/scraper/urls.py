from django.urls import path
from . import views

urlpatterns = [
    path('', views.scrape_channel, name='scrape_channel'),
    path('download/',views.download_excel, name = 'download_excel')
]