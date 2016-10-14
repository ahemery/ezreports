from django.contrib import admin
from.models import *


class EditeurAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'slug')
    ordering = ['libelle']


class BaseAdmin(admin.ModelAdmin):
    list_display = ('url', 'slug', 'editeur')
    ordering = ['url']


admin.site.register(Editeur, EditeurAdmin)
# admin.site.register(Library)
admin.site.register(Base, BaseAdmin)
# admin.site.register(Membership)
# admin.site.register(admin.site)
