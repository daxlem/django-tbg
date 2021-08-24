from django.db import models


class Cinema(models.Model):
    nid = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
    csv = models.FileField(upload_to='cinemas/csv/', help_text="Select the folder to upload", verbose_name='Import Data Files ')

    def __str__(self):
        return self.nid

    def delete(self, *args, **kwargs):
        self.csv.delete()
        super().delete(*args, **kwargs)
