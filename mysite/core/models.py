from django.db import models

class Cinema(models.Model):
    nid = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
    csv = models.FileField(upload_to='cinemas/csv/', help_text="Select the folder to upload", verbose_name='Import Data Files ')

    def __str__(self):
        return self.nid

    def delete(self, *args, **kwargs):
        self.csv.delete()
        super().delete(*args, **kwargs)

class DataCinema(models.Model):
    nid = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
    title = models.CharField(max_length=100),
    theatre_name = models.CharField(max_length=100),
    circuit = models.CharField(max_length=100),
    weekend_adm = models.IntegerField(),
    week_adm = models.IntegerField(),
    weekend_gross = models.DecimalField(max_digits=10, decimal_places=6),
    week_gross = models.DecimalField(max_digits=10, decimal_places=6),
    country = models.CharField(max_length=100),
    week_from = models.DateField(),
    week_to = models.DateField()

    def __str__(self):
        return self.nid