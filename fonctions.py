# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extras
import unicodedata

def s(txt,lg):
    #print txt,lg,type(txt)

    txt = unicode(txt,'utf-8')
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore')
    txt = (txt+u'                                                             ')[:lg]
    return txt

    #return (unicode(txt, 'utf-8')+u'                                                             ')[:lg]


def log(msg):
    syslog(str(msg))


def connect2postgres(postgres):
    cnx=False
    try:
        cnx = psycopg2.connect(\
            "dbname='"+postgres['dbname']+"'"+\
            "user='"+postgres['user']+"'"+\
            "host='"+postgres['host']+"'"+\
            "password='"+postgres['password']+"'"\
        )
    except Exception, e:
        resultat.append(u'ERREUR : Postgresql non disponible')
        sortie(resultat)
    cr = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cnx,cr

