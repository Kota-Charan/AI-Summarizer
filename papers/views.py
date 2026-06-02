from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from .forms import PaperUploadForm
from .models import ResearchPaper, Summary
from .utils import extract_text_from_pdf, generate_summary


def summary_page(request):
    latest_summary = Summary.objects.last()
    return render(request, 'papers/summary.html', {'summary': latest_summary})


def summary(request):
    return render(request, 'summary.html')


@login_required
def upload_paper(request):
    recent_summaries = Summary.objects.filter(paper__user=request.user).order_by('-id')[:2]

    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                paper = form.save(commit=False)
                paper.user = request.user
                paper.summary_size = form.cleaned_data['summary_size']
                paper.save()

                text = extract_text_from_pdf(paper.pdf_file.path)
                summary_size = form.cleaned_data['summary_size']
                summary_text = generate_summary(text, summary_size)

                if not summary_text:
                    summary_text = "Summary could not be generated."

                summary_obj = Summary.objects.create(
                    paper=paper,
                    summary_text=summary_text
                )

                return redirect('summary_detail', pk=summary_obj.id)
            except Exception as e:
                form.add_error(None, f"Error: {str(e)}")
    else:
        form = PaperUploadForm()

    return render(request, 'papers/upload.html', {'form': form, 'recent_summaries': recent_summaries})


def summary_detail(request, pk):
    summary = get_object_or_404(Summary, id=pk)
    return render(request, 'papers/summary.html', {'summary': summary})


def download_summary(request, pk):
    summary = get_object_or_404(Summary, pk=pk)

    file_title = summary.paper.title if summary.paper.title else f"summary_{pk}"
    safe_title = file_title.replace(' ', '_')
    filename = f'summary_{pk}_{safe_title}.pdf'

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    buffer = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    left_margin = inch
    right_margin = inch
    top_margin = inch
    bottom_margin = inch
    max_width = width - left_margin - right_margin
    line_height = 14
    page_number = 1

    def draw_page_border():
        buffer.setStrokeColorRGB(0, 0, 0)
        buffer.setLineWidth(1)
        buffer.rect(
            left_margin / 2,
            bottom_margin / 2,
            width - left_margin,
            height - bottom_margin,
            stroke=1,
            fill=0,
        )

    def draw_page_number():
        buffer.setFont('Helvetica-Oblique', 9)
        buffer.drawRightString(width - right_margin, bottom_margin * 0.5, f"Page {page_number}")

    def new_page():
        nonlocal page_number, y
        draw_page_number()
        buffer.showPage()
        page_number += 1
        y = height - top_margin
        buffer.setFont('Helvetica', 11)
        draw_page_border()

    y = height - top_margin
    draw_page_border()

    title_text = f"AI Summary for: {summary.paper.title}"
    buffer.setFont('Helvetica-Bold', 16)
    buffer.drawString(left_margin, y, title_text)
    y -= 24

    subtitle = f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}"
    buffer.setFont('Helvetica', 10)
    buffer.drawString(left_margin, y, subtitle)
    y -= 20

    buffer.setStrokeColorRGB(0.7, 0.7, 0.7)
    buffer.setLineWidth(0.5)
    buffer.line(left_margin, y, width - right_margin, y)
    y -= 16
    buffer.setFont('Helvetica', 11)

    paragraphs = summary.summary_text.split('\n')
    for paragraph in paragraphs:
        words = paragraph.split(' ')
        current_line = ''

        for word in words:
            test_line = (current_line + ' ' + word).strip()
            if pdfmetrics.stringWidth(test_line, 'Helvetica', 11) <= max_width:
                current_line = test_line
            else:
                if y < bottom_margin + line_height:
                    new_page()
                buffer.drawString(left_margin, y, current_line)
                y -= line_height
                current_line = word

        if current_line:
            if y < bottom_margin + line_height:
                new_page()
            buffer.drawString(left_margin, y, current_line)
            y -= line_height

        if paragraph.strip() == '':
            y -= line_height
        else:
            y -= line_height / 2

    draw_page_number()
    buffer.save()

    return response


@login_required
def history_page(request):
    summaries = Summary.objects.filter(paper__user=request.user).order_by('-id')
    return render(request, 'papers/history.html', {'summaries': summaries})