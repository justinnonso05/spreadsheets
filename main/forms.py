from django import forms

class FileUploadForm(forms.Form):
    file = forms.FileField(label='Upload CSV or Excel file')
