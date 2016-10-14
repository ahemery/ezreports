from django.conf import settings


def links(request):


    links = (
        {'name': 'dashboard', 'class': 'fa-dashboard', 'text': 'Dashboard'},
        {'name': 'connexions', 'class': 'fa-reddit-alien', 'text': 'Connexions'},
        {'name': 'consultations', 'class': 'fa-weibo', 'text': 'Consultations'},
        {'name': 'imports', 'class': 'fa-simplybuilt', 'text': 'Imports'},
    )

    return {'links': links}
