from django.urls import path
from .views import upload_paper
from . import views

urlpatterns = [
    path('', upload_paper, name='upload'),
    path('summary/', views.summary, name='summary'),
    path('summary/<int:pk>/', views.summary_detail, name='summary_detail'),
    
]