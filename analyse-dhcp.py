#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
import time
import pytz
import psycopg2
import psycopg2.extras


#** Lecture des paramètres *****************************************************
resultat=[]
if len(sys.argv)!=2:
    resultat.append(u'Paramètre attendu : ')
    resultat.append(u'- Fichier de configuration')
    sortie(resultat)
fichier_de_config = sys.argv[1]
#*******************************************************************************


#** Lecture du fichier de configuration ****************************************
try:
    exec(open(fichier_de_config).read(), globals()) # le fichier de configuration doit contenir le tableau 'parametres'
except Exception, err:
    resultat.append(u'Fichier de configuration non valide : err='+err)
    sortie(resultat)
if 'parametres' not in globals():
    resultat.append(u"Le fichier de configuration ne contient pas de variable 'parametres'")
    sortie(resultat)
p=parametres
postgres  = p.get('postgres')
odoo_glpi = p.get('odoo_glpi')
#*******************************************************************************


#** Connexion à odoo-glpi ******************************************************
if postgres and odoo_glpi:
    cnx=False
    try:
        cnx = psycopg2.connect("dbname='"+postgres['dbname']+"' user='"+postgres['user']+"' host='"+postgres['host']+"' password='"+postgres['password']+"'")
    except Exception, e:
        resultat.append(u'ERREUR : Postgresql non disponible')
        sortie(resultat)
    cr = cnx.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#*******************************************************************************



lines = open('/var/lib/dhcp/dhcpd.leases', 'r') 
ip=''
mac=''
dhcp_end=''
dhcp_hostname=''
for line in lines: 
    l=line.strip()
    t=l.split(' ')
    if len(t)>0:
        if t[0]=='lease':
            ip=t[1].strip()
        if t[0]=='ends':
            txt=t[2].strip()+' '+t[3].strip()[:8]
            dhcp_end=datetime.strptime(txt, '%Y/%m/%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        

        if t[0]=='hardware':
            mac=t[2].strip().upper()[:17]
        if t[0]=='client-hostname':
            t2=t[1].strip().split('"')
            dhcp_hostname=t2[1].upper()


            #** Recherche si cette adresse MAC existe déjà *********************
            SQL="""
                SELECT id,adresse_mac,adresse_ip
                FROM is_equipement_reseau
                WHERE adresse_mac='"""+mac+"""'
                ORDER BY date_modification desc
                limit 1
            """
            cr.execute(SQL)
            rows = cr.fetchall()
            equipement_id=False
            for row in rows:
                equipement_id=row['id']
            #*******************************************************************


            #** Recherche si ordinateur existe déjà ****************************
            SQL="""
                SELECT id
                FROM is_ordinateur
                WHERE name='"""+dhcp_hostname+"""'
                ORDER BY id desc
                limit 1
            """
            cr.execute(SQL)
            rows = cr.fetchall()
            ordinateur_id=False
            for row in rows:
                ordinateur_id=row['id']
            #*******************************************************************

            print mac,ip,dhcp_end,dhcp_hostname,equipement_id,ordinateur_id

            #** Enregistrement dans odoo-glpi **********************************
            if postgres and odoo_glpi and cr:
                site_id = odoo_glpi['site_id']
                mk=int(time.time())
                action='Maj'
                if equipement_id:
                    SQL="""
                        UPDATE is_equipement_reseau SET 
                            adresse_ip='"""+str(ip)+"""', 
                            date_modification='"""+str(datetime.utcfromtimestamp(mk))+"""',
                            origine_modification='dhcp',
                            dhcp_end='"""+str(dhcp_end)+"""',
                        """
                    if ordinateur_id:
                        SQL=SQL+"ordinateur_id="+str(ordinateur_id)+","
                    SQL=SQL+"""
                            dhcp_hostname='"""+str(dhcp_hostname)+"""' 
                        WHERE id="""+str(equipement_id)+"""
                    """
                else:
                    action='Création'
                    SQL="""
                        INSERT INTO is_equipement_reseau (date_creation,date_modification,origine_modification,site_id,adresse_ip,adresse_mac,active) 
                        VALUES (
                            '"""+str(datetime.utcfromtimestamp(mk))+"""',
                            '"""+str(datetime.utcfromtimestamp(mk))+"""',
                            'dhcp',
                            '"""+str(site_id)+"""', 
                            '"""+str(ip)+"""', 
                            '"""+str(mac)+"""',
                            't'
                    ) """
                cr.execute(SQL)
                cnx.commit()
            #*******************************************************************






exit()


#** Analyse du réseau avec nmap ************************************************
cde="nmap -n -sP "+nmap+" 2>&1"
lines=os.popen(cde).readlines()
IP=''
MAC=''
for line in lines:
    l=line.strip()
    t=l.split(' ')
    if len(t)>0:
        if t[0]=='Nmap':
            IP=t[4].strip()
        if t[0]=='MAC':
            MAC=t[2].strip()


#*******************************************************************************











