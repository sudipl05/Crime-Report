import os
import requests
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from .forms import RegisterForm, ReportForm
from .models import Report
from django.core.mail import EmailMessage
from django.utils.timezone import localtime
from django.urls import reverse

# ✅ Register View
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            print("✅ Form is valid")
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"]
            )

            # Admin login link
            current_site = get_current_site(request)
            login_url = f"http://192.168.18.49:8000{reverse('login')}"
        
            # Send welcome email
            try:
                send_mail(
                    subject='Welcome to Crime Report System',
                    message = (
                        f'Hello {user.username},\n'
                        'Thank you for registering at our website. You can now report crimes and view your submissions anytime.\n'
                        f'Login here:\n {login_url}'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print("✅ Welcome email sent.")
            except Exception as e:
                print(f"❌ Failed to send welcome email: {e}")

            

            # Notify admins
            admin_emails = [u.email for u in User.objects.filter(is_staff=True).exclude(id=user.id) if u.email]
            try:
                if admin_emails:
                    email = EmailMessage(
                        subject='New user registered',
                        body=f"A new user {user.username} has registered.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=admin_emails
                    )
                    email.send()
            except Exception as e:
                print(f"❌ Failed to notify admins: {e}")

            login(request, user)
            messages.success(request, '✅ Registered successfully! You are now logged in.')
            return redirect('login')  # change as per your app
        else:
            print("❌ Form errors:", form.errors)

    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


# ✅ Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    return render(request, 'users/login.html')


# ✅ Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    # Get location filter from the URL query parameters (if any)
    location_filter = request.GET.get('location', '')  # Default to an empty string if not provided
    
    # If a location filter is provided, filter reports by location
    if location_filter:
        reports = Report.objects.filter(user=request.user, location__icontains=location_filter).order_by('-created_at')
    else:
        # If no location filter, fetch all reports for the user, ordered by creation date
        reports = Report.objects.filter(user=request.user).order_by('-created_at')
    
    # Pass the filtered (and ordered) reports to the template
    return render(request, 'users/dashboard.html', {'reports': reports})

@login_required
def report_view(request):
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()

            # ✅ Generate PDF
            pdf_buffer = BytesIO()
            pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
            pdf.setFont("Helvetica", 12)

            y = 750
            pdf.drawString(72, y, "Crime Report")
            y -= 20
            pdf.drawString(72, y, f"Submitted by: {report.user.username}")
            y -= 20
            pdf.drawString(72, y, f"Title: {report.title}")
            y -= 20
            pdf.drawString(72, y, f"Description: {report.description}")
            y -= 20
            pdf.drawString(72, y, f"Location: {report.location}")
            y -= 20
            local_created_at = localtime(report.created_at)
            pdf.drawString(72, y, f"Date Reported: {local_created_at.strftime('%Y-%m-%d %H:%M')}")
            y -= 20

            # ✅ Add photo if exists
            if report.photos:
                try:
                    photo_path = report.photos.path
                    pdf.drawString(72, y, "Attached Photo:")
                    y -= 40
                    image_height = 200
                    pdf.drawImage(photo_path, 72, y - image_height, width=200, height=image_height)
                    y -= (image_height + 20)
                except Exception as e:
                    pdf.drawString(72, y, f"Photo Error: {str(e)}")
                    y -= 20
            else:
                pdf.drawString(72, y, "No photo uploaded.")
                y -= 20

            # ✅ Add video link if exists
            y_cursor = y - 60
            if report.videos and hasattr(report.videos, 'url'):
                try:
                    video_url = request.build_absolute_uri(report.videos.url).replace('127.0.0.1', '192.168.18.49')
                    video_path = report.videos.path
                    video_name = os.path.basename(video_path)

                    pdf.drawString(72, y, "Attached video:")
                    y -= 15
                    pdf.drawString(72, y, f"Filename: {video_name}")
                    y-= 15

                    text = "Click here to watch the video"
                    text_width = stringWidth(text, 'Helvetica', 12)

                    pdf.setFillColorRGB(0, 0, 1)  # Blue text for link
                    pdf.drawString(72, y, text)
                    pdf.linkURL(video_url, (72, y, 72 + text_width, y + 12), relative=0)
                    pdf.setFillColorRGB(0, 0, 0)
                    y -= 40  # Adjust if you want space below the link
                except Exception as e:
                    pdf.drawString(72, y, f"Video link error: {str(e)}")
                    y -= 20
            else:
                pdf.drawString(72, y, "No video uploaded.")
                y -= 15


            # ✅ Finalize and send PDF
            pdf.showPage()
            pdf.save()
            pdf_buffer.seek(0)
            # ✅ Email with attachment
            admin_emails = [user.email for user in User.objects.filter(is_staff=True) if user.email]
            email = EmailMessage(
                subject='New Crime Report Submitted',
                body=f"A new report was submitted by {report.user.username}.\nPlease see attached PDF.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=admin_emails
            )
            email.attach(f"crime_report_by_{report.user.username}.pdf", pdf_buffer.read(), 'application/pdf')
            email.send()

            messages.success(request, 'Your report has been submitted successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'There was an error with your submission. Please check the form.')
    else:
        form = ReportForm()

    return render(request, 'users/report.html', {'form': form})


# ✅ Edit Report View
@login_required
def edit_report_view(request, report_id):
    report = get_object_or_404(Report, id=report_id, user=request.user)

    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES, instance=report)
        if form.is_valid():
            form.save()
            print("✅ Report updated successfully.")
            return redirect('dashboard')
        else:
            print("❌ Form is not valid:", form.errors)  # Add this
    else:
        form = ReportForm(instance=report)

    return render(request, 'users/edit_report.html', {
        'form': form,
        'report': report
    })

# ✅ Delete Report View
@login_required
def delete_report(request, pk):
    report = get_object_or_404(Report, pk=pk, user=request.user)
    if request.method == 'POST':
        report.delete()
        return redirect('dashboard')


# ✅ Download Report as PDF
@login_required
def download_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, user=request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setFont("Helvetica", 12)

    # Basic info
    y = 750
    pdf.drawString(72, y, f"Title: {report.title}")
    y -= 15
    pdf.drawString(72, y, f"Description: {report.description}")
    y -= 15
    pdf.drawString(72, y, f"Location: {report.location}")
    y -= 15
    local_created_at = localtime(report.created_at)
    pdf.drawString(72, y, f"Created at: {local_created_at.strftime('%Y-%m-%d %H:%M')}")
    y -= 25
     
    # Photo
    if report.photos:
        try:
            pdf.drawString(72, y, "Attached Photo:")
            y -= 15
            photo_path = report.photos.path
            image_height = 150
            pdf.drawImage(photo_path, 72, y - image_height, width=200, height=image_height)
            y -= image_height + 15
        except Exception as e:
            pdf.drawString(72, y, f"Error loading photo: {str(e)}")
            y -= 15
    else:
        pdf.drawString(72, y, "Photos: None")
        y -= 15


    # Video (local file)
    pdf.drawString(72, y, "Video:")
    y -= 15
    if report.videos:
        try:
            video_path = report.videos.path
            video_name = os.path.basename(video_path)
            pdf.drawString(90, y, f"Filename: {video_name}")
            y -= 15

            if hasattr(report.videos, 'url'):
                video_url = request.build_absolute_uri(report.videos.url)
                text = "Click here to watch the video"
                text_width = stringWidth(text, 'Helvetica', 12)
                pdf.setFillColorRGB(0, 0, 1)
                pdf.drawString(90, y, text)
                pdf.linkURL(video_url, (90, y, 90 + text_width, y + 12), relative=0)
                pdf.setFillColorRGB(0, 0, 0)
                y -= 25
        except Exception as e:
            pdf.drawString(90, y, f"Error loading video: {str(e)}")
            y -= 15
    else:
        pdf.drawString(90, y, "No video uploaded.")
        y -= 15

    # Finalize PDF
    pdf.showPage()
    pdf.save()
    return response
