from django.shortcuts import render
from .models import *
from django.shortcuts import get_object_or_404, render


def login_view(request):
    return render(request, 'login.html',
    {

    })


def logout_view(request):
    return render(request, 'logout.html',
    {

    })


def dashboard_view(request):

    return render(request, 'dashboard.html',
    {

    })


def connexions_view(request):

    return render(request, 'connexions.html',
    {

    })


def consultations_view(request):

    return render(request, 'consultations.html',
    {

    })


def plateformes_view(request):

    bases = Base.objects.all().order_by('url')
    editeurs = Editeur.objects.all().order_by('libelle')

    return render(request, 'plateformes.html',
    {
        'bases': bases,
        'editeurs': editeurs,
    })


def params_view(request):

    return render(request, 'params.html',
    {

    })


def editeur_view(request, slug):

    editeur = get_object_or_404(Editeur, slug=slug)
    bases = Base.objects.filter(editeur=editeur)

    return render(request, 'editeur.html',
    {
        'editeur': editeur,
        'bases': bases,
    })


def base_view(request, slug):

    base = get_object_or_404(Base, slug=slug)

    return render(request, 'base.html',
    {
        'base': base,
    })

