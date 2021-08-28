from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from mysite.core import views


urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('cinema/', views.cinema_list, name='cinema_list'),
    path('cinema/upload/', views.upload_cinema, name='upload_cinema'),
    path('cinema/<int:pk>/', views.delete_cinema, name='delete_cinema'),
    path('class/cinema/delete', views.delete_cinema_all, name='delete_cinema_all'),
    path('class/cinema/', views.CinemaListView.as_view(), name='class_cinema_list'),
    path('class/cinema/upload/', views.UploadCinemaView.as_view(), name='class_upload_cinema'),
    path('class/cinema/reports/', views.Reports.as_view(), name='reports'),
    path('class/cinema/reports/process', views.generate_report, name='generate_report'),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
