from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataCinema',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('theatre_name', models.CharField(max_length=100)),
                ('circuit', models.CharField(max_length=100)),
                ('weekend_adm', models.IntegerField()),
                ('week_adm', models.IntegerField()),
                ('weekend_gross', models.DecimalField(10,6)),
                ('week_gross', models.DecimalField(10,6)),
                ('country', models.CharField(max_length=100)),
                ('week_from', models.DateField()),
                ('week_to', models.DateField()),
            ],
        ),
    ]