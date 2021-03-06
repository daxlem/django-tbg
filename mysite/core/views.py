from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.core.files.storage import FileSystemStorage
from django.urls import reverse_lazy
from django.contrib import messages
from os.path import isfile, join
from sqlalchemy import create_engine
import pandas as pd
import os
from datetime import datetime
import warnings

from .forms import CinemaForm
from .models import Cinema
from .models import DataCinema

class Home(TemplateView):
    template_name = 'home.html'
    warnings.filterwarnings("ignore")

class Reports(TemplateView):
    template_name = 'reports.html'

class Dashboards(TemplateView):
    template_name = 'dashboards.html'

def upload_cinema(request):
    context = {}
    files = request.FILES.getlist('csv')
    for f in files:
        form = CinemaForm(request.POST, request.FILES)
        file_csv = Cinema(csv=f)
        file_csv.save()
    read_cinema_all(request)
    return render(request, 'upload_cinema.html', {'form': form})

def read_cinema_all(request):
    df_list = []
    dfGeneral = pd.DataFrame()
    dfDatabase = pd.DataFrame()
    engine = create_engine('sqlite:///tbgdb.sqlite3')
    path = './media/cinemas/csv/'
    files = [f for f in os.listdir(path) if isfile(join(path, f))]

    if len(files) > 0:
        for f in files:            
            file_path = path+f
            read_file = pd.read_excel (file_path)
            read_file.to_csv ("Data.csv", index = None)
            df_title = pd.DataFrame(pd.read_csv("Data.csv"))
            df_title = df_title.iloc[0][0]
            country = df_title.split(',')[0]
            week = df_title.split(',')[2]
            week = week.replace('Week of ','')
            week = week.replace('Week of ','')
            date_from = week.split(' to ')[0]
            date_from = date_from.split(' ')[1]
            date_to = week.split(' to ')[1]
            year = date_to.split('/')[2]
            date_from = date_from+'/'+year
            if date_from > date_to:
                date_from = week.split(' to ')[0]
                year = int(year) - 1
                date_from = date_from.split(' ')[1]+'/'+ str(year)
            df = pd.DataFrame(pd.read_csv("Data.csv", header=2)).assign(country=country, week_from=date_from, week_to=date_to)
            column_names = df.columns
            column_names = column_names.str.replace('$','dollar')
            column_names = column_names.str.lower()
            column_names = column_names.str.replace(' ','_')
            column_names = column_names.str.replace('\n','_')
            column_names = column_names.str.replace('_dollar','')
            delete_columns = (0,2,3,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,24,25,26,27,28,29,30,30,31,32,33,35,36,37,38,39,40,41,43,44,45)
            df.columns = column_names
            df_clean = df.drop(df.columns[[delete_columns]], axis = 1, inplace = False)
            df_clean['title'] = df_clean['title'].astype(str)
            df_clean['theatre_name'] = df_clean['theatre_name'].astype(str)
            df_clean['circuit'] = df_clean['circuit'].astype(str)
            df_clean['weekend_adm'] = df_clean['weekend_adm'].astype(int)
            df_clean['week_adm'] = df_clean['week_adm'].astype(int)
            df_clean['weekend_gross'] = df_clean['weekend_gross'].astype(float)
            df_clean['week_gross'] = df_clean['week_gross'].astype(float)
            df_clean['country'] = df_clean['country'].astype(str)
            df_clean['week_from'] = pd.to_datetime(df_clean['week_from'])
            df_clean['week_from'] = df_clean['week_from'].dt.strftime('%d/%m/%Y')
            df_clean['week_to'] = pd.to_datetime(df_clean['week_to'])
            df_clean['week_to'] = df_clean['week_to'].dt.strftime('%d/%m/%Y')
            pd.options.display.float_format = "{:,.2f}".format
            pd.set_option("colheader_justify", "center")
            df_list.append(df_clean)
        dfGeneral = pd.concat(df_list)
    else:
        messages.error(request, "No Files Uploaded")

    if not dfGeneral.empty:
        dfDatabase = dfGeneral
        dfDatabase.to_sql(DataCinema._meta.db_table, if_exists='replace', con=engine, index=False)

    df_clean = dfGeneral.to_html(classes='table table-striped', index=False)
    return print('DataFrames Loaded')

def generate_report(request):
    dfGeneral = pd.DataFrame()
    df_clean = pd.DataFrame()
    path = './media/cinemas/csv/'
    files = [f for f in os.listdir(path) if isfile(join(path, f))]

    if len(files) > 0:
        if request.method == 'POST':
            data = []
            engine = create_engine('sqlite:///tbgdb.sqlite3')
            to_date = request.POST['to_date']
            from_date = request.POST['from_date']
            country = request.POST['country']
            report = request.POST['report']
            parameter_time = request.POST['parameter-week']
            report_title = ""

            if not (to_date and from_date) == "":
                msg_date_from = datetime.strptime((from_date), '%Y-%m-%d')
                msg_date_to = datetime.strptime((to_date), '%Y-%m-%d')

                if (report == "Admissions by Country"):
                    query = 'SELECT cd.country AS country, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country union all SELECT "Total", SUM(cd.@week_adm) FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)
                
                if (report == "Gross by Country"):
                    query = 'SELECT cd.country AS country, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country union all SELECT "Total", SUM(cd.@week_gross) FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Admissions by Circuit - General"):
                    query = 'SELECT cd.country ,cd.circuit , sum(cd.@week_adm) as total from core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" group by country,circuit order by country;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country","Circuit","Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['-t','Total', total_sum]
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(float)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Total Admissions']), axis=1)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(str).apply(lambda x: x.replace('.0',''))
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Gross by Circuit - General"):
                    query = 'SELECT cd.country, cd.circuit, sum(cd.@week_gross) as total from core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" group by country,circuit order by country;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country","Circuit","Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(float)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['-t','Total', total_sum]
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(float)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Admissions by Country and Circuit"):
                    query = 'SELECT cd.country AS country, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country union all SELECT "Total", SUM(cd.@week_adm) FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        
                        query = 'SELECT country AS CountryCircuit, circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE Circuit IN (SELECT circuit AS Circuit FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY SUM(@week_adm) DESC LIMIT 3) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY country,circuit ORDER BY CircuitAdm ASC;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        Share = pd.read_sql_query(query,engine)
                        print(Share)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Country']
                                title_circuit = row['CountryCircuit']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)
                                                                               
                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=circuit_adm

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Admissions']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                    

                        dfGeneral[topCircuits[0]] = dfGeneral[topCircuits[0]].astype(int)
                        dfGeneral[topCircuits[0]] = dfGeneral.apply(lambda x: "{:,}".format(x[topCircuits[0]]), axis=1)
                        dfGeneral[topCircuits[1]] = dfGeneral[topCircuits[1]].astype(int)
                        dfGeneral[topCircuits[1]] = dfGeneral.apply(lambda x: "{:,}".format(x[topCircuits[1]]), axis=1)
                        dfGeneral[topCircuits[2]] = dfGeneral[topCircuits[2]].astype(int)
                        dfGeneral[topCircuits[2]] = dfGeneral.apply(lambda x: "{:,}".format(x[topCircuits[2]]), axis=1)

                        query = 'SELECT "Total", SUM(cd.@week_adm) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Total Admissions'] = row['CircuitAdm']
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t'+str(row['CircuitAdm'])
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Gross by Country and Circuit"):
                    query = 'SELECT cd.country AS country, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country union all SELECT "Total", SUM(cd.@week_gross) FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        
                        query = 'SELECT country AS CountryCircuit, circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE Circuit IN (SELECT circuit AS Circuit FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY SUM(@week_gross) DESC LIMIT 3) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY country,circuit ORDER BY CircuitAdm ASC;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(round((row['CircuitAdm']),2))

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Country']
                                title_circuit = row['CountryCircuit']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)
                                                                                                                       
                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=round(circuit_adm,2)

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Admissions']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                    

                        dfGeneral[topCircuits[0]] = dfGeneral[topCircuits[0]].astype(float)
                        dfGeneral[topCircuits[0]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[0]]), axis=1)
                        dfGeneral[topCircuits[1]] = dfGeneral[topCircuits[1]].astype(float)
                        dfGeneral[topCircuits[1]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[1]]), axis=1)
                        dfGeneral[topCircuits[2]] = dfGeneral[topCircuits[2]].astype(float)
                        dfGeneral[topCircuits[2]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[2]]), axis=1)

                        query = 'SELECT "Total", SUM(cd.@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TotalCircuit = pd.read_sql_query(query,engine)
                        
                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Total Admissions'] = round((row['CircuitAdm']),2)
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t$'+str(round((row['CircuitAdm']),2))
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                        dfGeneral.round(2)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(float)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - General Admissions"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_adm DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum]
                        query = 'SELECT "Ranking", "Total", SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" LIMIT 1;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        Result = pd.read_sql_query(query,engine)
                        headers = ["Rank","Title", "Total Admissions"]
                        dfTotal = pd.DataFrame(Result)
                        dfTotal.columns = headers
                        dfGeneral = dfGeneral.append(Result)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - General Gross"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_gross DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        total_sum = dfGeneral['Total Gross ($)'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum]
                        query = 'SELECT "Ranking", "Total", SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" LIMIT 1;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Result = pd.read_sql_query(query,engine)
                        headers = ["Rank","Title", "Total Gross ($)"]
                        dfTotal = pd.DataFrame(Result)
                        dfTotal.columns = headers
                        dfGeneral = dfGeneral.append(Result)
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)
                        
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - Country Admissions"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_adm DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    query = query.replace('@country_name',country)
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | ' + country + ' | ' 
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum]
                        query = 'SELECT "Ranking", "Total", SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" LIMIT 1;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        Result = pd.read_sql_query(query,engine)
                        headers = ["Rank","Title", "Total Admissions"]
                        dfTotal = pd.DataFrame(Result)
                        dfTotal.columns = headers
                        dfGeneral = dfGeneral.append(Result)
                        dfGeneral['Total Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Total Admissions']), axis=1)
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - Country Gross"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_gross DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    query = query.replace('@country_name',country)
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | ' + country + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        total_sum = dfGeneral['Total Gross ($)'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum]
                        query = 'SELECT "Ranking", "Total", SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" LIMIT 1;'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Result = pd.read_sql_query(query,engine)
                        headers = ["Rank", "Title", "Total Gross ($)"]
                        dfTotal = pd.DataFrame(Result)
                        dfTotal.columns = headers
                        dfGeneral = dfGeneral.append(Result)
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)
                        
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - General Admissions by Circuit"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_adm DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers                   

                    if not (dfGeneral.iloc[0][1] is None):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")

                        query = 'SELECT title AS CircuitTitle, circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_adm) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY title,circuit ORDER BY CircuitAdm ASC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_adm) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Title']
                                title_circuit = row['CircuitTitle']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)

                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=circuit_adm

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Admissions']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                         

                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum,'--'+str(totalCircuits[0]),'--','--'+str(totalCircuits[1]),'--','--'+str(totalCircuits[2]),'--']

                        query = 'SELECT "Total", SUM(cd.@week_adm) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Rank'] = 'Ranking'
                                    dfGeneral.at[6,'Title'] = 'Total'
                                    dfGeneral.at[6,'Total Admissions'] = row['CircuitAdm']
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t'+str(row['CircuitAdm'])
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(str).apply(lambda x: x.replace('.0',''))
                        
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - General Gross by Circuit"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_gross DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                    
                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")

                        query = 'SELECT title AS CircuitTitle, circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY title,circuit ORDER BY CircuitAdm ASC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Title']
                                title_circuit = row['CircuitTitle']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)

                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=round(circuit_adm,2)

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Gross ($)']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                         

                        dfGeneral[topCircuits[0]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[0]]), axis=1)
                        dfGeneral[topCircuits[1]] = dfGeneral[topCircuits[1]].astype(float)
                        dfGeneral[topCircuits[1]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[1]]), axis=1)
                        dfGeneral[topCircuits[2]] = dfGeneral[topCircuits[2]].astype(float)
                        dfGeneral[topCircuits[2]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[2]]), axis=1)

                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        total_sum = dfGeneral['Total Gross ($)'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', (round(total_sum,2)),'--$'+str(round(totalCircuits[0],2)),'--','--$'+str(round(totalCircuits[1],2)),'--','--$'+str(round(totalCircuits[2],2)),'--']
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)

                        query = 'SELECT "Total", SUM(cd.@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Rank'] = 'Ranking'
                                    dfGeneral.at[6,'Title'] = 'Total'
                                    dfGeneral.at[6,'Total Gross ($)'] = '$'+str(round(row['CircuitAdm'],2))
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t$'+str(round(row['CircuitAdm'],2))
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - Country Admissions by Circuit"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_adm) AS @week_adm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_adm DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    query = query.replace('@country_name',country)
                    if(parameter_time=="week"):
                        query = query.replace('@week_adm','week_adm')
                    else:
                        query = query.replace('@week_adm','weekend_adm')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | ' + country + ' | ' 
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        query = 'SELECT title AS CircuitTitle, circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND title IN (SELECT cd.title AS title FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_adm) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY title,circuit ORDER BY CircuitAdm ASC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND title IN (SELECT cd.title AS title FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_adm) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Title']
                                title_circuit = row['CircuitTitle']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)

                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=circuit_adm

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Admissions']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                         

                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(int)
                        total_sum = dfGeneral['Total Admissions'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', total_sum,'--'+str(totalCircuits[0]),'--','--'+str(totalCircuits[1]),'--','--'+str(totalCircuits[2]),'--']

                        query = 'SELECT "Total", SUM(cd.@week_adm) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_adm) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_adm','week_adm')
                        else:
                            query = query.replace('@week_adm','weekend_adm')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Rank'] = 'Ranking'
                                    dfGeneral.at[6,'Title'] = 'Total'
                                    dfGeneral.at[6,'Total Admissions'] = row['CircuitAdm']
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t'+str(row['CircuitAdm'])
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                        dfGeneral['Total Admissions'] = dfGeneral['Total Admissions'].astype(str).apply(lambda x: x.replace('.0',''))
                        
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - Country Gross by Circuit"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_gross DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    query = query.replace('@country_name',country)
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    
                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | ' + country + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        query = 'SELECT title AS CircuitTitle, circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND title IN (SELECT cd.title AS title FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY title,circuit ORDER BY CircuitAdm ASC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND title IN (SELECT cd.title AS title FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Title']
                                title_circuit = row['CircuitTitle']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)

                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=round(circuit_adm,2)

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Gross ($)']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                         

                        dfGeneral[topCircuits[0]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[0]]), axis=1)
                        dfGeneral[topCircuits[1]] = dfGeneral[topCircuits[1]].astype(float)
                        dfGeneral[topCircuits[1]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[1]]), axis=1)
                        dfGeneral[topCircuits[2]] = dfGeneral[topCircuits[2]].astype(float)
                        dfGeneral[topCircuits[2]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[2]]), axis=1)

                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        total_sum = dfGeneral['Total Gross ($)'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', (round(total_sum,2)),'--$'+str(round(totalCircuits[0],2)),'--','--$'+str(round(totalCircuits[1],2)),'--','--$'+str(round(totalCircuits[2],2)),'--']
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)

                        query = 'SELECT "Total", SUM(cd.@week_gross) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE cd.country="@country_name" AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        query = query.replace('@country_name',country)
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Rank'] = 'Ranking'
                                    dfGeneral.at[6,'Title'] = 'Total'
                                    dfGeneral.at[6,'Total Gross ($)'] = '$'+str(round(row['CircuitAdm'],2))
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t$'+str(round(row['CircuitAdm'],2))
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                                
                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Top 5 Movies - General Gross by Circuit"):
                    query = 'SELECT cd.title AS title, SUM(cd.@week_gross) AS @week_gross FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY @week_gross DESC LIMIT 5;'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    if(parameter_time=="week"):
                        query = query.replace('@week_gross','week_gross')
                    else:
                        query = query.replace('@week_gross','weekend_gross')
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Total Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers
                    dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                    
                    if (dfGeneral.empty == False):
                        if(parameter_time=="week"):
                            report_title = 'Week Report | '
                        else:
                            report_title = 'Weekend Report | '
                        report_title = report_title + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")

                        query = 'SELECT title AS CircuitTitle, circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY title,circuit ORDER BY CircuitAdm ASC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        Share = pd.read_sql_query(query,engine)
                        
                        query = 'SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE title IN (SELECT cd.title AS title FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(cd.@week_gross) DESC LIMIT 5) AND substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC LIMIT 3'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TopShare = pd.read_sql_query(query,engine)

                        topCircuits = []
                        totalCircuits = []
                        totalesGeneral = []

                        for index, row in TopShare.iterrows():
                            topCircuits.append(row['Circuit'])
                            totalCircuits.append(row['CircuitAdm'])

                        for index, row in Share.iterrows():
                            for index2, titles in dfGeneral.iterrows():
                                title_top = titles['Title']
                                title_circuit = row['CircuitTitle']
                                circuit_top = row['Circuit']
                                circuit_adm = row['CircuitAdm']

                                if (circuit_top in topCircuits) and (title_circuit in title_top):
                                    if not (circuit_top in dfGeneral.columns):
                                        data = ["0.00","0.00","0.00","0.00","0.00"]
                                        data2 = ["0","0","0","0","0"]
                                        dfGeneral.insert(2, column=topCircuits[0], value=data2)
                                        dfGeneral.insert(3, column='SHR% [1]', value=data)
                                        dfGeneral.insert(4, column=topCircuits[1], value=data2)
                                        dfGeneral.insert(5, column='SHR% [2]', value=data)
                                        dfGeneral.insert(6, column=topCircuits[2], value=data2)
                                        dfGeneral.insert(7, column='SHR% [3]', value=data)

                                    if (circuit_top in dfGeneral.columns):
                                        if(title_circuit==title_top):
                                            dfGeneral.at[index2,circuit_top]=round(circuit_adm,2)

                        for index, row in dfGeneral.iterrows():
                            total_adm = dfGeneral.iloc[index]['Total Gross ($)']

                            if (float(dfGeneral.iloc[index][topCircuits[0]]))>0.00:
                                circuit_adm1 = round((dfGeneral.iloc[index][topCircuits[0]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = circuit_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index][topCircuits[1]]))>0.00:
                                circuit_adm2 = round((dfGeneral.iloc[index][topCircuits[1]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = circuit_adm2
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00
                            
                            if (float(dfGeneral.iloc[index][topCircuits[2]]))>0.00:
                                circuit_adm3 = round((dfGeneral.iloc[index][topCircuits[2]]/total_adm)*100,2)
                                dfGeneral.at[index,'SHR% [3]'] = circuit_adm3
                            else:
                                dfGeneral.at[index,'SHR% [3]'] = 0.00                         

                        dfGeneral[topCircuits[0]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[0]]), axis=1)
                        dfGeneral[topCircuits[1]] = dfGeneral[topCircuits[1]].astype(float)
                        dfGeneral[topCircuits[1]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[1]]), axis=1)
                        dfGeneral[topCircuits[2]] = dfGeneral[topCircuits[2]].astype(float)
                        dfGeneral[topCircuits[2]] = dfGeneral.apply(lambda x: "${:,.2f}".format(x[topCircuits[2]]), axis=1)

                        data = ["1","2","3","4","5"]
                        dfGeneral.insert(loc=0, column='Rank', value=data)
                        dfGeneral['Total Gross ($)'] = dfGeneral['Total Gross ($)'].astype(float)
                        total_sum = dfGeneral['Total Gross ($)'].sum()
                        dfGeneral.loc[len(dfGeneral.index)] = ['--','Total Top 5', (round(total_sum,2)),'--$'+str(round(totalCircuits[0],2)),'--','--$'+str(round(totalCircuits[1],2)),'--','--$'+str(round(totalCircuits[2],2)),'--']
                        dfGeneral['Total Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Total Gross ($)']), axis=1)

                        query = 'SELECT "Total", SUM(cd.@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" UNION ALL SELECT circuit AS Circuit, SUM(@week_gross) AS CircuitAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY circuit ORDER BY CircuitAdm DESC'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        if(parameter_time=="week"):
                            query = query.replace('@week_gross','week_gross')
                        else:
                            query = query.replace('@week_gross','weekend_gross')
                        TotalCircuit = pd.read_sql_query(query,engine)

                        for index, row in TotalCircuit.iterrows():
                            if ((row['"Total"']) in dfGeneral.columns) or ((row['"Total"'])=='Total'):
                                if((row['"Total"'])=='Total'):
                                    dfGeneral.at[6,'Rank'] = 'Ranking'
                                    dfGeneral.at[6,'Title'] = 'Total'
                                    dfGeneral.at[6,'Total Gross ($)'] = '$'+str(round(row['CircuitAdm'],2))
                                else:
                                    dfGeneral.at[6,row['"Total"']] = '-t$'+str(round(row['CircuitAdm'],2))
                                    dfGeneral.at[6,'SHR% [1]'] = '-t'
                                    dfGeneral.at[6,'SHR% [2]'] = '-t'
                                    dfGeneral.at[6,'SHR% [3]'] = '-t'                               

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - General Admissions"):
                    query = 'SELECT cd.country AS Country, SUM(week_adm) AS WeekAdm, SUM(weekend_adm) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Week Admissions", "Weekend Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Week Admissions'] = dfGeneral['Week Admissions'].astype(int)
                        dfGeneral['Weekend Admissions'] = dfGeneral['Weekend Admissions'].astype(int)
                        week_adm_sum = dfGeneral['Week Admissions'].sum()                        
                        weekend_adm_sum = dfGeneral['Weekend Admissions'].sum()

                        data = ["0.00","0.00","0.00","0.00","0.00","0.00"]
                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Week Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Week Admissions']/week_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Weekend Admissions']/weekend_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Week Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Week Admissions']), axis=1)
                        dfGeneral['Weekend Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Weekend Admissions']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t'+str(week_adm_sum),'-t'+str(shr1_sum),'-t'+str(weekend_adm_sum),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - General Gross"):
                    query = 'SELECT cd.country AS Country, SUM(week_gross) AS WeekAdm, SUM(weekend_gross) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.country'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Country", "Week Gross ($)", "Weekend Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Week Gross ($)'] = dfGeneral['Week Gross ($)'].astype(float)
                        dfGeneral['Weekend Gross ($)'] = dfGeneral['Weekend Gross ($)'].astype(float)
                        week_gross_sum = dfGeneral['Week Gross ($)'].sum()                       
                        weekend_gross_sum = dfGeneral['Weekend Gross ($)'].sum()

                        data = ["0.00","0.00","0.00","0.00","0.00","0.00"]
                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Week Gross ($)']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Week Gross ($)']/week_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Gross ($)']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Weekend Gross ($)']/weekend_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Week Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Week Gross ($)']), axis=1)
                        dfGeneral['Weekend Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Weekend Gross ($)']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t$'+str(round(week_gross_sum,2)),'-t'+str(shr1_sum),'-t$'+str(round(weekend_gross_sum,2)),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - Top 5 Movies Admissions"):
                    query = 'SELECT cd.title AS Title, SUM(week_adm) AS WeekAdm, SUM(weekend_adm) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(week_adm) DESC LIMIT 5'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Week Admissions", "Weekend Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Week Admissions'] = dfGeneral['Week Admissions'].astype(int)
                        dfGeneral['Weekend Admissions'] = dfGeneral['Weekend Admissions'].astype(int)
                        week_adm_sum = dfGeneral['Week Admissions'].sum()                        
                        weekend_adm_sum = dfGeneral['Weekend Admissions'].sum()

                        data = ["0.00","0.00","0.00","0.00","0.00"]
                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Week Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Week Admissions']/week_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Weekend Admissions']/weekend_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Week Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Week Admissions']), axis=1)
                        dfGeneral['Weekend Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Weekend Admissions']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t'+str(week_adm_sum),'-t'+str(shr1_sum),'-t'+str(weekend_adm_sum),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - Top 5 Movies Gross"):
                    query = 'SELECT cd.title AS Title, SUM(week_gross) AS WeekAdm, SUM(weekend_gross) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.title ORDER BY SUM(week_gross) DESC LIMIT 5'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Title", "Weekend Gross ($)", "Weekend Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Weekend Gross ($)'] = dfGeneral['Weekend Gross ($)'].astype(float)
                        dfGeneral['Weekend Admissions'] = dfGeneral['Weekend Admissions'].astype(float)
                        week_gross_sum = dfGeneral['Weekend Gross ($)'].sum()                        
                        weekend_gross_sum = dfGeneral['Weekend Admissions'].sum()

                        data = ["0.00","0.00","0.00","0.00","0.00"]
                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Weekend Gross ($)']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Weekend Gross ($)']/week_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Admissions']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Weekend Admissions']/weekend_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Weekend Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Weekend Gross ($)']), axis=1)
                        dfGeneral['Weekend Admissions'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Weekend Admissions']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t$'+str(round(week_gross_sum,2)),'-t'+str(shr1_sum),'-t$'+str(round(weekend_gross_sum,2)),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - Circuit Admissions"):
                    query = 'SELECT cd.circuit AS Circuit, SUM(week_adm) AS WeekAdm, SUM(weekend_adm) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.circuit ORDER BY SUM(week_adm) DESC'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Circuit", "Week Admissions", "Weekend Admissions"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Week Admissions'] = dfGeneral['Week Admissions'].astype(int)
                        dfGeneral['Weekend Admissions'] = dfGeneral['Weekend Admissions'].astype(int)
                        week_adm_sum = dfGeneral['Week Admissions'].sum()                        
                        weekend_adm_sum = dfGeneral['Weekend Admissions'].sum()

                        query = 'SELECT COUNT(DISTINCT cd.circuit) AS countCircuit from core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        circuit_count = engine.execute(query)
                        count = circuit_count.fetchone()[0]
                        data = ["0.00"]*int(count)
                        
                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Week Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Week Admissions']/week_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Admissions']))>0.00:
                                week_adm1 = round((dfGeneral.iloc[index]['Weekend Admissions']/weekend_adm_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_adm1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Week Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Week Admissions']), axis=1)
                        dfGeneral['Weekend Admissions'] = dfGeneral.apply(lambda x: "{:,}".format(x['Weekend Admissions']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t'+str(week_adm_sum),'-t'+str(shr1_sum),'-t'+str(weekend_adm_sum),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                if (report == "Week vs Weekend - Circuit Gross"):
                    query = 'SELECT cd.circuit AS Circuit, SUM(week_gross) AS WeekAdm, SUM(weekend_gross) AS WeekendAdm FROM core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to" GROUP BY cd.circuit ORDER BY SUM(week_adm) DESC'
                    query = query.replace('@week_from',from_date.replace('-',''))
                    query = query.replace('@week_to', to_date.replace('-',''))
                    Result = pd.read_sql_query(query,engine)
                    headers = ["Circuit", "Week Gross ($)", "Weekend Gross ($)"]
                    dfGeneral = pd.DataFrame(Result)
                    dfGeneral.columns = headers

                    if not (dfGeneral.iloc[0][1] is None):
                        report_title = 'Report | ' + report + ' | '
                        report_title = report_title + msg_date_from.strftime("%b %d %Y")
                        report_title = report_title + ' - '
                        report_title = report_title + msg_date_to.strftime("%b %d %Y")
                        dfGeneral['Week Gross ($)'] = dfGeneral['Week Gross ($)'].astype(float)
                        dfGeneral['Weekend Gross ($)'] = dfGeneral['Weekend Gross ($)'].astype(float)
                        week_gross_sum = dfGeneral['Week Gross ($)'].sum()                       
                        weekend_gross_sum = dfGeneral['Weekend Gross ($)'].sum()

                        query = 'SELECT COUNT(DISTINCT cd.circuit) AS countCircuit from core_data cd WHERE substr(week_from,7)||substr(week_from,4,2)||substr(week_from,1,2) >= "@week_from" AND substr(week_to,7)||substr(week_to,4,2)||substr(week_to,1,2) <= "@week_to";'
                        query = query.replace('@week_from',from_date.replace('-',''))
                        query = query.replace('@week_to', to_date.replace('-',''))
                        circuit_count = engine.execute(query)
                        count = circuit_count.fetchone()[0]
                        data = ["0.00"]*int(count)

                        dfGeneral.insert(2, column='SHR% [1]', value=data)
                        dfGeneral.insert(4, column='SHR% [2]', value=data)

                        for index, row in dfGeneral.iterrows():
                            if (float(dfGeneral.iloc[index]['Week Gross ($)']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Week Gross ($)']/week_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [1]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [1]'] = 0.00

                            if (float(dfGeneral.iloc[index]['Weekend Gross ($)']))>0.00:
                                week_gross1 = round((dfGeneral.iloc[index]['Weekend Gross ($)']/weekend_gross_sum)*100,2)
                                dfGeneral.at[index,'SHR% [2]'] = week_gross1
                            else:
                                dfGeneral.at[index,'SHR% [2]'] = 0.00

                        dfGeneral['Week Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Week Gross ($)']), axis=1)
                        dfGeneral['Weekend Gross ($)'] = dfGeneral.apply(lambda x: "${:,.2f}".format(x['Weekend Gross ($)']), axis=1)
                        dfGeneral['SHR% [1]'] = dfGeneral['SHR% [1]'].astype(float)
                        dfGeneral['SHR% [2]'] = dfGeneral['SHR% [2]'].astype(float)

                        shr1_sum = round(dfGeneral['SHR% [1]'].sum(),0)
                        shr2_sum = round(dfGeneral['SHR% [2]'].sum(),0)
                        dfGeneral.loc[len(dfGeneral.index)] = ['Total','-t$'+str(round(week_gross_sum,2)),'-t'+str(shr1_sum),'-t$'+str(round(weekend_gross_sum,2)),'-t'+str(shr2_sum)]

                    else:
                        dfGeneral = pd.DataFrame()
                        msg = 'No Records between '+ msg_date_from.strftime("%b %d %Y")
                        msg = msg + ' and ' 
                        msg = msg + msg_date_to.strftime("%b %d %Y")
                        messages.warning(request, msg)

                table_title = 'text-center">'+'\n<h5 style="margin-bottom: 20px; text-align: center;">'
                table_title = table_title + report_title
                table_title = table_title + '</h5>'

                df_clean = dfGeneral.to_html(classes='table table-striped table-bordered text-center', justify='center', index=False)
                df_clean = df_clean.replace('<table','<table style="overflow: scroll;"')
                df_clean = df_clean.replace('<thead>','<thead class="thead-dark">')
                df_clean = df_clean.replace('<tr style="text-align: center;">','<tr class="thead-dark" style="text-align: center;">')
                df_clean = df_clean.replace('<th>','<th scope="col">')
                df_clean = df_clean.replace('<td>--','<td bgcolor= "#708090" style="color:white; font-weight: bold">')
                df_clean = df_clean.replace('<td>-t','<td bgcolor= "black" style="color:white; font-weight: bold">')
                df_clean = df_clean.replace('<td>Ranking</td>','<td bgcolor= "black" style="color:white; font-weight: bold"></td>')
                df_clean = df_clean.replace('<td>Total Top 5</td>\n      <td>','<td bgcolor= "#708090" style="color:white; font-weight: bold">Total Top 5</td>\n      <td bgcolor= "#708090" style="color:white; font-weight: bold">')
                df_clean = df_clean.replace('<td>Total</td>\n      <td>','<td bgcolor= "black" style="color:white; font-weight: bold">Total</td>\n      <td bgcolor= "black" style="color:white; font-weight: bold">')
                df_clean = df_clean.replace('<td>Total</td>','<td bgcolor= "black" style="color:white; font-weight: bold">Total</td>')
                df_clean = df_clean.replace('text-center">',table_title)
            else:
                messages.error(request, "Date Fields Required")
                df_clean = dfGeneral.to_html(classes='table table-striped table-bordered text-center', justify='center', index=False)
    else:
        messages.error(request, "No Files Uploaded")
        df_clean = dfGeneral.to_html(classes='table table-striped table-bordered text-center', justify='center', index=False)

    return render(request, 'reports.html', {'table': df_clean})

def cinema_list(request):
    cinemas = Cinema.objects.all()
    return render(request, 'cinema_list.html', {
        'cinemas': cinemas
    })

def delete_cinema(request, pk):
    engine = create_engine('sqlite:///tbgdb.sqlite3')
    if request.method == 'POST':
        cinema = Cinema.objects.get(pk=pk)
        cinema.delete()
        messages.success(request, "File Deleted")
        engine.execute('DROP TABLE IF EXISTS core_data;') 
        read_cinema_all(request)
    return redirect('class_cinema_list')

def delete_cinema_all(request):
    path = './media/cinemas/csv/'
    files = [f for f in os.listdir(path) if isfile(join(path, f))]

    if len(files) > 0:
        engine = create_engine('sqlite:///tbgdb.sqlite3')
        if request.method == 'POST':
            files = Cinema.objects.all()
            for f in files:
                pk = f.pk
                cinema = Cinema.objects.get(pk=pk)
                cinema.delete()
        messages.success(request, "All Files Deleted")
        engine.execute('DROP TABLE IF EXISTS core_data;')
    else:
        messages.error(request, "No Files Uploaded")   
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