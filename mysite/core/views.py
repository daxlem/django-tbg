from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy
from django.contrib import messages
from os.path import isfile, join
import pandas as pd
import os
import warnings

from .forms import CinemaForm
from .models import Cinema

class Home(TemplateView):
    template_name = 'home.html'
    warnings.filterwarnings("ignore")

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
    df_list = []
    path = './media/cinemas/csv/'
    files = [f for f in os.listdir(path) if isfile(join(path, f))]
    for f in files:
        file_path = path+f
        read_file = pd.read_excel (file_path)
        read_file.to_csv ("Data.csv", index = None)
        df_title = pd.DataFrame(pd.read_csv("Data.csv"))
        df_title = df_title.iloc[0][0]
        country = df_title.split(',')[0]
        week = df_title.split(',')[2]
        week = week.replace('Week of ','')
        date_from = week.split(' to ')[0]
        date_to = week.split(' to ')[1]
        year = date_to.split('/')[2]
        date_from = date_from+'/'+year
        df = pd.DataFrame(pd.read_csv("Data.csv", header=2)).assign(Country=country, WeekFrom=date_from, WeekTo=date_to)
        delete_columns = (0,2,3,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,24,25,26,27,28,29,30,30,31,32,33,35,36,37,38,39,40,41,43,44,45)
        df_clean = df.drop(df.columns[[delete_columns]], axis = 1, inplace = False)
        df_list.append(df_clean)
    
    dfGeneral = pd.concat(df_list)
    df_clean = dfGeneral.to_html(classes='table table-hover', index=False)
    return render(request, 'reports.html', {'table': df_clean})

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