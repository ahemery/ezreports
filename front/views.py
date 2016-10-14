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


def imports_view(request):

    bases = Base.objects.all().order_by('url')
    plateformes = Plateforme.objects.all().order_by('libelle')

    return render(request, 'imports.html',
    {
        'bases': bases,
        'plateformes': plateformes,
    })


def params_view(request):

    return render(request, 'params.html',
    {

    })


def plateforme_view(request, slug):

    plateforme = get_object_or_404(Plateforme, slug=slug)
    bases = Base.objects.filter(plateforme = plateforme)

    return render(request, 'plateforme.html',
    {
        'plateforme': plateforme,
        'bases': bases,
    })


def base_view(request, slug):

    base = get_object_or_404(Base, slug=slug)

    return render(request, 'base.html',
    {
        'base': base,
    })

