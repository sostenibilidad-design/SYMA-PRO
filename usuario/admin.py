from django.contrib import admin
from .models import Usuario

# Esto hace que el Usuario aparezca en el panel
admin.site.register(Usuario)