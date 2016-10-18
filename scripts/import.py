import glob
from datetime import datetime
import re
import json
import os
from django.db import connection


conf = {
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
  "path": "/mnt/data/dev/scd/ezpaarse/logs/*.log",
}


def run():

    print("toto")
    return

    # Expression régulière pour les log d'ezproxy
    regex = "^(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3}) - " \
            "(?P<login>[0-9a-zA-Z]*) .*" \
            "\[(?P<datetime>.*)\].*connect\?session=.*&url=" \
            "https?://w*\.?(?P<url>.[^/]*)/(?P<path>.*) HTTP/1.1.*"
    login = re.compile(regex)


    config = json.load(open('config.json'))
    bases = config['bases']

    #try:
        # Connexion à la base sql
        # conn = mysql.connector.connect(**config['sql'])
        # sql = conn.cursor()
    with connection.cursor() as cursor:

        # Pour chaque fichier de log à traiter
        for logfile in sorted(glob.glob(config['path'])):

            print("{}: ".format(os.path.basename(logfile)))

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


        # sql.close()
        # conn.close()

    # except mysql.connector.Error as err:
    #     print("Something went wrong: {}".format(err))




