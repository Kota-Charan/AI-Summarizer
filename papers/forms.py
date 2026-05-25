from django import forms
from .models import ResearchPaper

class PaperUploadForm(forms.ModelForm):
    class Meta:
        model = ResearchPaper
        fields = ['title', 'pdf_file']