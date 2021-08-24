# django-tbg
Cinema App - Proyecto de Trabajo de grado

Para su instalación se requiere la versión de Python 3.9 en el equipo.

La instalación del proyecto se lleva a cabo ejecutando los siguientes comandos en PowerShell:

1- Ubicarse en el directorio del proyecto:
cd C:\Users\Public\django-tbg

2- Crear el virtual environment del proyecto, con los siguientes requerimientos.
pipenv install -r .\requirements.txt

3- Activar el virtual enviroment creado
pipenv shell

4- Ejecutar las migraciones del proyecto
python .\manage.py migrate

5- Crear un super usuario (user: admin pass: admin)
python .\manage.py createsuperuser

6- Finalmente ejecutamos el servidor
python .\manage.py runserver

Para acceder al proyecto, abrimos un navegador en la url http://127.0.0.1:8000/
