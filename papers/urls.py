from django.urls import path
from .views import upload_paper, summary_page, summary_detail, download_summary, history_page

urlpatterns = [
    path('', upload_paper, name='upload'),
    path('summary/', summary_page, name='summary'),
    path('summary/<int:pk>/', summary_detail, name='summary_detail'),
    path('download/<int:pk>/', download_summary, name='download_summary'),
    path('history/', history_page, name='history'),
]