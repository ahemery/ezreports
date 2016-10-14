from django.shortcuts import render

# Create your views here.


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

    return render(request, 'imports.html',
    {

    })

