from django.shortcuts import render

# Create your views here.

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

    return render(request, 'imports.html',
    {

    })


def params_view(request):

    return render(request, 'params.html',
    {

    })

