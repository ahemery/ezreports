from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404, render
from datetime import datetime, timedelta
from django.db.models import Count, F

def login_view(request):
    return render(request, 'login.html',
    {

    })


def logout_view(request):
    return render(request, 'logout.html',
    {

    })


def dashboard_view(request):

    ressources = Lien.objects.all()
    return render(request, 'dashboard.html',
    {
        'ressources': ressources,
    })


def connexions_view(request):

    start = datetime.now() - timedelta(days=90)
    connexions = Connexion.objects\
        .values('date')\
        .filter(date__gte=start)\
        .annotate(total=Count('date'))\
        .order_by('date')

    tops = Connexion.objects\
        .values('lien__ressource')\
        .filter(date__year=str(datetime.now().year))\
        .annotate(total=Count('lien__ressource'))\
        .annotate(ressource=F('lien__ressource__libelle'))\
        .annotate(ressource_slug=F('lien__ressource__slug'))\
        .order_by('-total')[:15]

    return render(request, 'connexions.html',
    {
        'connexions': connexions,
        'start': start,
        'tops': tops,
    })


def consultations_view(request):

    return render(request, 'consultations.html',
    {

    })


def ressources_view(request):

    liens = Lien.objects.all().order_by('url')
    editeurs = Editeur.objects.all().order_by('libelle')

    return render(request, 'ressources.html',
    {
        'liens': liens,
        'editeurs': editeurs,
    })


def ressource_view(request, slug):

    ressource = get_object_or_404(Ressource, slug=slug)
    liens = Lien.objects.filter(ressource=ressource).order_by('lien')
    editeur = Editeur.objects.get(id=ressource.editeur_id)

    return render(request, 'ressource.html',
    {
        'ressource': ressource,
        'editeur': editeur,
        'liens': liens,
    })


def params_view(request):

    return render(request, 'params.html',
    {

    })


def editeur_view(request, slug):

    editeur = get_object_or_404(Editeur, slug=slug)
    ressources = Ressource.objects.filter(editeur=editeur).order_by('libelle')

    return render(request, 'editeur.html',
    {
        'editeur': editeur,
        'ressources': ressources,
    })


def editeurs_view(request):

    editeurs = Editeur.objects.all().order_by('libelle')

    return render(request, 'editeurs.html',
    {
        'editeurs': editeurs,
    })


def lien_view(request, slug):
    lien = get_object_or_404(Lien, slug=slug)

    return render(request, 'base.html',
    {
        'lien': lien,
    })

