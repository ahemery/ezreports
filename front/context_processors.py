from django.conf import settings


def links(request):


    # Liste des sections à afficher dans la barre latérale gauche
    links = (
        {'name': 'dashboard', 'class': 'fa-dashboard', 'text': 'Dashboard'},
        # {'name': 'composantes', 'class': 'fa-reddit-alien', 'text': 'Connexions'},
        {'name': 'connexions', 'class': 'fa-reddit-alien', 'text': 'Connexions'},
        {'name': 'consultations', 'class': 'fa-weibo', 'text': 'Consultations'},
        {'name': 'editeurs', 'class': 'fa-stack-overflow', 'text': 'Editeurs'},
    )

    return {'links': links}
