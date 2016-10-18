from django.contrib import admin
from.models import *


class EditeurAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'slug')
    ordering = ['libelle']


class LienAdmin(admin.ModelAdmin):
    list_display = ('slug', 'url', 'ressource')
    ordering = ['slug']


class RessourceAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'slug', 'editeur')
    ordering = ['libelle']


admin.site.register(Editeur, EditeurAdmin)
admin.site.register(Lien, LienAdmin)
admin.site.register(Ressource, RessourceAdmin)
# admin.site.register(Membership)
# admin.site.register(admin.site)
