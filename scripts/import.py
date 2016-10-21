import glob
from datetime import datetime
import re
import os
from django.db import connection
from front.models import *
from django.db.models import Max

config = {
  "ldap": {
    "server": "ldap.univ-pau.fr",
    "dn": "cn=consultplus,ou=admin,dc=univ-pau,dc=fr",
    "pw": "uppaplus",
    "code": "ou=people,dc=univ-pau,dc=fr"
  },
  "ezpaarse": {
    "server": "http://ezpaarse.univ-pau.fr",
    "options": [
      "geoip: none",
      "Output-Fields: +datetime",
      "Crypted-Fields: none"
    ],
    "debug": "false"
  },
  "path": "/mnt/data/dev/scd/ezreports/logs/*.log",
}


def processconnexions(path, maxdate):
    """
    Récupère les connexions à partir du fichier de log d'ezproxy

    :param path Chemin d'accès des fichiers de log
    :param maxdate: Date à partir de laquelle on traite les connexions
    :return:
    """

    # Expression régulière pour les log d'ezproxy
    regex = "^(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3}) - " \
            "(?P<login>[0-9a-zA-Z]*) .*" \
            "\[(?P<datetime>.*)\].*connect\?session=.*&url=" \
            "https?://w*\.?(?P<url>.[^/]*)/(?P<path>.*) HTTP/1.1.*"
    login = re.compile(regex)

    # Pour chaque fichier de log à traiter
    for logfile in sorted(glob.glob(path)):

        # format du fichier 'ezproxy-YYYY.MM.DD.log'
        filename = os.path.split(logfile)[1]
        filedate = datetime.strptime(filename, 'ezproxy-%Y.%m.%d.log')

        if filedate <= maxdate:
            continue

        print("{}: ".format(os.path.basename(logfile)))

        with connection.cursor() as cursor:

            # Ouvre le fichier
            with open(logfile) as handle:

                # Pour chaque lignes
                for line in handle:

                    # Ca match ?
                    match = login.match(line)
                    if match:
                        url = match.group("url")
                        date = datetime.strptime(match.group("datetime"), '%d/%b/%Y:%H:%M:%S %z')

                        # Insertion du lien si inconnu
                        cursor.execute("INSERT INTO liens (url) SELECT %(url)s "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM liens WHERE url = %(url)s) LIMIT 1 ",
                            params={'url': url})

                        # Insertion de l'utilisateur si inconnu
                        cursor.execute("INSERT INTO utilisateurs (hash) SELECT md5(%(login)s) "
                                "FROM (SELECT 1) as tmp "
                                "WHERE NOT EXISTS(SELECT id FROM utilisateurs WHERE hash = md5(%(login)s)) LIMIT 1 ",
                            params={'login': match.group("login")})

                        # Insertion de la connexion
                        cursor.execute("INSERT INTO connexions  "
                                "SELECT NULL as id, %(date)s as date, %(time)s as time, md5(%(ip)s) as ip, "
                                "l.id as lien_id, u.id as utilisateur_id  "
                                "FROM utilisateurs u "
                                "LEFT JOIN liens l           on l.url = %(url)s "
                                "WHERE u.hash = md5(%(login)s) "
                                "AND NOT EXISTS (SELECT utilisateur_id FROM connexions WHERE "
                                "utilisateur_id = u.id AND lien_id = l.id AND date = %(date)s "
                                "AND time = %(time)s AND ip = md5(%(ip)s))",
                            params={'login': match.group("login"), 'url': url,
                                    'date': date.strftime("%Y-%m-%d"), 'time': date.strftime("%H:%M:%S"),
                                    'ip': match.group("ip")})

                        cursor.commit()


def run():

    #
    # Date du dernier fichier traité
    query = Connexion.objects.all().aggregate(Max('date'))
    maxdate = datetime(query['date__max'].year, query['date__max'].month, query['date__max'].day - 1)

    #
    # Importe les connexions
    #
    processconnexions(config['path'], maxdate)




