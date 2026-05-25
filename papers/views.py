from django.shortcuts import render, redirect
from .forms import PaperUploadForm
from .models import Summary
from .utils import extract_text_from_pdf, generate_summary
from django.contrib.auth.decorators import login_required
from .utils import extract_text_from_pdf

def upload_paper(request):

    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)

        if form.is_valid():

            paper = form.save(commit=False)
            paper.user = request.user
            paper.save()

            text = extract_text_from_pdf(
                paper.pdf_file.path
            )

            summary_text = generate_summary(text)

            Summary.objects.create(
                paper=paper,
                summary_text=summary_text
            )

            return redirect('summary')

    else:
        form = PaperUploadForm()

    return render(
        request,
        'papers/upload.html',
        {'form': form}
    )
def summary_page(request):

    latest_summary = Summary.objects.last()
    

    return render(
        request,
        'papers/summary.html',
        {'summary': latest_summary}
    )
def summary(request):
    return render(request, 'summary.html')

@login_required

def upload_paper(request):

    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)

        if form.is_valid():

            try:
                # 1. Save paper
                paper = form.save(commit=False)
                paper.user = request.user
                paper.save()

                # 2. Extract text safely
                text = extract_text_from_pdf(paper.pdf_file.path)

                if not text or "Error" in text:
                    form.add_error(None, "Could not read PDF properly.")
                    return render(request, 'papers/upload.html', {'form': form})

                # 3. Generate summary safely
                summary_text = generate_summary(text)

                # fallback safety
                if not summary_text:
                    summary_text = "Summary could not be generated."

                # 4. Save summary
                summary_obj = Summary.objects.create(
                    paper=paper,
                    summary_text=summary_text
                )

                # 5. Redirect (IMPORTANT FIX)
                return redirect('summary_detail', pk=summary_obj.id)

            except Exception as e:
                form.add_error(None, f"Error: {str(e)}")

    else:
        form = PaperUploadForm()

    return render(request, 'papers/upload.html', {'form': form})
def summary_detail(request, pk):
    summary = Summary.objects.get(id=pk)
    return render(request, 'papers/summary.html', {
        'summary': summary
    })