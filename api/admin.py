from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.

# admin.site.register(User)

@admin.register(User)

class CustomeUserDispaly(UserAdmin):

    fieldsets = list(UserAdmin.fieldsets) + [((None,{'fields':('role',)}))]

    add_fieldsets = list(UserAdmin.add_fieldsets) + [((None,{'fields':('role',)}))]

    list_display = list(UserAdmin.list_display) + [('role')]