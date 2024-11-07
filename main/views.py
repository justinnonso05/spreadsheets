from django.shortcuts import render
import plotly.express as px
import plotly.io as pio
import pandas as pd
from .forms import FileUploadForm

def graphs(request):
    # Sample data for the graph
    df = px.data.iris()

    # Create a Plotly figure
    fig = px.scatter(df, x='sepal_width', y='sepal_length', color='species')

    # Convert the Plotly figure to HTML
    plot_div = pio.to_html(fig, full_html=False)

    return render(request, 'main/index.html', {'plot_div': plot_div})

from django.shortcuts import render, redirect
import plotly.express as px
import plotly.io as pio
import pandas as pd
from .forms import FileUploadForm
import os

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


from django.core.mail import send_mail
from django.conf import settings
import pandas as pd
import os

def sendEmails(request):
    file_path = request.session.get('file_path')
    emails_sent = []

    if not file_path or not os.path.exists(file_path):
        return render(request, 'main/email_error.html', {'error': 'File not found or session expired.'})

    try:
        # Load the data and find the 'email' column
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        else:
            return render(request, 'main/email_error.html', {'error': 'Unsupported file format.'})

        if 'Emails' not in data.columns:
            return render(request, 'main/email_error.html', {'error': 'No "email" column found in the file.'})

        # Retrieve email addresses and send emails
        email_addresses = data['Emails'].dropna().unique()
        subject = "Your Subject Here"
        message = "Your email body here"
        from_email = settings.DEFAULT_FROM_EMAIL

        for email in email_addresses:
            try:
                send_mail(subject, message, from_email, [email])
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
