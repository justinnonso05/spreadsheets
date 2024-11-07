from django.shortcuts import render
import plotly.express as px
import plotly.io as pio
import pandas as pd
from .forms import FileUploadForm
from django.core.mail import send_mail
from django.conf import settings
import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def graphs(request):
    # Sample data for the graph
    df = px.data.iris()

    # Create a Plotly figure
    fig = px.scatter(df, x='sepal_width', y='sepal_length', color='species')

    # Convert the Plotly figure to HTML
    plot_div = pio.to_html(fig, full_html=False)

    return render(request, 'main/index.html', {'plot_div': plot_div})


def dataView(request):
    form = FileUploadForm()
    data = None
    plot_div = None

    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_path = f"{uploaded_file.name}"

            # Save the file temporarily for the email view
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Store file path in the session for access in the email-sending view
            request.session['file_path'] = file_path

            # Process the file and create visualizations
            try:
                if uploaded_file.name.endswith('.csv'):
                    data = pd.read_csv(file_path)
                elif uploaded_file.name.endswith('.xls') or uploaded_file.name.endswith('.xlsx'):
                    data = pd.read_excel(file_path)
                else:
                    form.add_error('file', 'Unsupported file type')

                if data is not None:
                    # Create some example plots
                    bar_graph = px.histogram(data, x=data.columns[0], y=data.columns[1], title="Bar Plot")
                    bar_plot_div = pio.to_html(bar_graph, full_html=False)
                    pie_chart = px.pie(data, names=data.columns[0], values=data.columns[1], title="Pie Chart")
                    pie_plot_div = pio.to_html(pie_chart, full_html=False)

                    plot_div = f"{bar_plot_div}<br><br>{pie_plot_div}"

            except Exception as e:
                form.add_error('file', f'Error processing file: {e}')

    context = {
        "form": form,
        "data": data,
        'plot_div': plot_div
    }

    return render(request, 'main/upload.html', context)


def sendEmails(request):
    file_path = request.session.get('file_path')
    emails_sent = []

    if not file_path or not os.path.exists(file_path):
        return render(request, 'main/email_error.html', {'error': 'File not found or session expired.'})

    try:
        # Load the data
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        else:
            return render(request, 'main/email_error.html', {'error': 'Unsupported file format.'})

        # Check for required columns
        if 'Emails' not in data.columns or len(data.columns) < 2:
            return render(request, 'main/email_error.html', {'error': 'File must contain "Emails" and a voting code column.'})

        # Retrieve email addresses and corresponding voting codes
        email_addresses = data['Emails'].dropna().unique()
        voting_codes = data.iloc[:, 1]  # Assuming the next column after 'Emails' contains the voting codes

        # Send each email with its corresponding voting code
        subject = "Your Voting Code"
        from_email = settings.DEFAULT_FROM_EMAIL

        for email, voting_code in zip(email_addresses, voting_codes):
            # Render the HTML email template with context
            html_content = render_to_string('main/email_content.html', {
                'email': email,
                'voting_code': voting_code
            })
            # Create the email message
            email_message = EmailMultiAlternatives(subject, '', from_email, [email])
            email_message.attach_alternative(html_content, "text/html")
            
            try:
                email_message.send()
                emails_sent.append(email)
            except Exception as e:
                print(f'Error sending email to {email}: {e}')  # Log error for debugging

    except Exception as e:
        return render(request, 'main/email_error.html', {'error': f'Error processing file: {e}'})
    
    # Optionally delete the file after sending emails
    os.remove(file_path)
    del request.session['file_path']

    context = {'emails_sent': emails_sent}
    return render(request, 'main/email_success.html', context)