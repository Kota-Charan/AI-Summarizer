from django import forms
from .models import ResearchPaper

class PaperUploadForm(forms.ModelForm):
    SIZE_CHOICES = [
        ('small', 'Small (Quick Snippet)'),
        ('medium', 'Medium (Standard Overview)'),
        ('large', 'Large (Comprehensive Review)'),
    ]
    summary_size = forms.ChoiceField(
        choices=SIZE_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'})
    )

    class Meta:
        model = ResearchPaper
        fields = ['title', 'pdf_file', 'summary_size']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Attention Is All You Need',
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'file-upload-input'
            }),
        }