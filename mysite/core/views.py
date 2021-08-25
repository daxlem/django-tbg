from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy
from django.contrib import messages
from os.path import isfile, join
import pandas as pd
import os


from .forms import CinemaForm
from .models import Cinema

class Home(TemplateView):
    template_name = 'home.html'

class Reports(TemplateView):
    template_name = 'reports.html'

def upload_cinema(request):
    context = {}
    files = request.FILES.getlist('csv')
    for f in files:
        form = CinemaForm(request.POST, request.FILES)
        file_csv = Cinema(csv=f)
        file_csv.save()    
    return render(request, 'upload_cinema.html', {'form': form})

def read_cinema_all(request):
    path = './media/cinemas/csv/'
    files = [f for f in os.listdir(path) if isfile(join(path, f))]
    for f in files:
        file_path = path+f
        read_file = pd.read_excel (file_path)
        read_file.to_csv ("Data.csv", index = None)
        df_title = pd.DataFrame(pd.read_csv("Data.csv"))
        df = pd.DataFrame(pd.read_csv("Data.csv", header=2))
        df_title = df_title.iloc[0][0]
        print(df)
        print(df_title)
        dfprint = df.to_html(classes='table mb-0', index=False)
    return render(request, 'reports.html', {'table': dfprint})

def cinema_list(request):
    cinemas = Cinema.objects.all()
    return render(request, 'cinema_list.html', {
        'cinemas': cinemas
    })

def delete_cinema(request, pk):
    if request.method == 'POST':
        cinema = Cinema.objects.get(pk=pk)
        cinema.delete()
        messages.success(request, "File Deleted")
    return redirect('class_cinema_list')

def delete_cinema_all(request):
    if request.method == 'POST':
        files = Cinema.objects.all()
        for f in files:
            pk = f.pk
            cinema = Cinema.objects.get(pk=pk)
            cinema.delete()
        messages.success(request, "All Files Deleted")    
    return redirect('class_cinema_list')

class CinemaListView(ListView):
    model = Cinema
    template_name = 'class_cinema_list.html'
    context_object_name = 'cinemas'


class UploadCinemaView(CreateView):
    form_class = CinemaForm
    success_url = reverse_lazy('class_cinema_list') # want different url for every instance
    template_name = 'upload_cinema.html' # same for template_name

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            upload_cinema(request)
            messages.success(self.request, "Files Uploaded")
            return redirect(self.success_url)            
        else:
            return render(request, self.template_name, {'form': form})