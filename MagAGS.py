#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Programme de suivi de l'état de charge SOC de la batterie et contrôle 
# de la génératrice selon des seuils minimum et maxmimum.
# Ce programme a été fait pour remplacer le module ME-BMK de Magnum-Energy
# qui a des problèmes à effectuer le suivi du SOC de la batterie.
#
# Auteur: Daniel Cote, Mars 2025
# 

import logging
import sqlite3
import time
from conf import getconf
from relay import Relay
from manage_gen import manage_gen

# Convertit les niveaux de sévérité en leur valeurs de type int
# Retourne 20 par défaut si aucun match.

def llevel(level):
    ''' Convertit les niveaux de sévérité en leur valeurs de type int
        Retourne 20 par défaut si aucun match.
    '''
    if level == 'DEBUG':
        return 10
    if level == 'INFO':
        return 20
    if level == 'WARNING':
        return 30
    if level == 'ERROR':
        return 40
    if level == 'CRITICAL':
        return 50
    return 20

def cvtstate(state):
    if state == True:
        return 'ON'
    return 'OFF'

def getcurrentstate(relay):
    try:
        if relay.state(1) is True:
            return 'ON'
        else:
            return 'OFF'
    except Exception as e:
        log.error(f"Erreur lors de la lecture de l'état du relais: {e}")
        return "Inconnu... Erreur lors de la lecture de l'état du relais"

# ===========Programme Principal=======================================================

#configure logging.
fmt = '%(asctime)s %(levelname)s %(lineno)s %(message)s'
logging.basicConfig(level=getconf('ll'), filename=getconf('lf'), format=fmt)
log = logging.getLogger('MagAGS')

log.setLevel(llevel(getconf('ll')))
log.info("Début du programme")
log.info("Log Level = %s", getconf('ll'))

# Détermination de l'enregistrement des conditions d'opération
ftype = getconf('ftype')


# Backup des paramêtres de configuration
llevelb = ''

# Intervale de temps
interval = 60 # boucle aux 60 secondes

# Condition de la boucle sans fin. Si la valeur change, on sort de la boucle.
cmd = 'RUN'

frun = None

# Connexion à la base de données
conn = sqlite3.connect("../monitormidnite/monitormidnite.db")
curs = conn.cursor()

# Objet relay
relay = Relay(idVendor=0x16c0, idProduct=0x05df)
# Turn all switches off
relay.state(0, on=False)

while cmd == 'RUN':
    start = time.time()
    log.setLevel(llevel(getconf('ll')))
    log.debug("Bouclage... %s", time.ctime())

    cmd = getconf('cmd')

    # Valeurs des SOC min et max
    SOCmin = int(getconf('SOCsetpoints')[0:2])
    SOCmax = int(getconf('SOCsetpoints')[2:4])

    ftype = getconf('ftype')
    ftxt = getconf('ftxt')
    fSQLite = getconf('fSQLite')

    genctrl = getconf('genctrl')

    # Lecture du dernier enregistrement de la table des données opérationnelles avec
    # l'horodateur et l'état de charge de la batterie
    curs.execute("select dtm, soc from onem order by dtm desc limit 1")
    onem_dtm, onem_soc = curs.fetchone()
    
    if genctrl == "AUTO":

        # Détermination du besoin de démarrage ou de l'arrêt de la génératrice
        resp =manage_gen(onem_soc, SOCmin, SOCmax, relay)
        log.debug(f"dtm={onem_dtm}, SOCmin={SOCmin}, SOC={onem_soc}, SOCmax={SOCmax}, resp = {resp}, currentstate={getcurrentstate(relay)}")

        # Contrôle du relais selon le besoin de démarrage ou de l'arrêt de la génératrice
        if resp == "ON":
            relay.state(1, on=True)
            log.debug("Generator auto on")
        if resp == "OFF":
            relay.state(1, on=False)
            log.debug("Generator auto off")
        log.debug(f"dtm={onem_dtm}, SOCmin={SOCmin}, SOC={onem_soc}, SOCmax={SOCmax}, resp={resp}, currentstate={getcurrentstate(relay)}")
    elif genctrl == "ON":
        resp = "MANUAL ON"
        relay.state(1, on=True)
        log.debug("Generator manual ON")
    elif genctrl == "OFF":
        resp = "MANUAL OFF"
        relay.state(1, on=False)
        log.debug("Generator manual OFF")
    
# Écriture de l'état dans un fichier texte pour communiquer l'état à d'autres programmes
    if ftype == 'txt':
        ftxt = "test.txt"
        with open(getconf('ftxt'), "w") as f:
            f.write(f"{onem_dtm},{SOCmin},{onem_soc},{SOCmax},{resp},{getcurrentstate(relay)}\n")
# Écriture de l'état dans une table SQLite3 seulement lors d'un changement de statut.
    if ftype == 'sql':
        if frun is None: # On lit les dernières valeurs au démarrage du programme
            log.debug("première run... On lit le dernier enregistrement de la table.")
            conn = sqlite3.connect(fSQLite)
            curs1 = conn.cursor()
            curs1.execute("SELECT * FROM magagss")
            seq, dtm, gencontrol, start_limit, soc, stop_limit, expected_state, relay_state = curs1.fetchone()
            conn.close()
            frun = 1

        conn = sqlite3.connect(fSQLite)
# Pour magags, on enregistre que si il y a un changement avec l'enregistrement précédent
        if gencontrol != genctrl or start_limit != SOCmin or stop_limit != SOCmax \
            or expected_state != resp or relay_state != getcurrentstate(relay):
            print(f"Différences dans les enregistrements... {onem_dtm}")
            conn.execute("""
            INSERT INTO magags VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, getcurrentstate(relay)))
            gencontrol = genctrl
            start_limit = SOCmin
            soc = onem_soc
            stop_limit = SOCmax
            expected_state = resp
            relay_state = getcurrentstate(relay)

# On conserve toujours le dernier état dans magagss dans un seul enregistrement
        conn.execute("""
        INSERT OR REPLACE INTO magagss VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (1, onem_dtm, genctrl, SOCmin, onem_soc, SOCmax, resp, getcurrentstate(relay)))
        conn.commit()        
        conn.close()
        
        
# Gestion de la temporisation et sortie du programme
    duration = time.time() - start
    delay = interval - duration
    if delay > 0:
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            cmd = 'STOP'
            conn.close()
            break

log.info("Fin de la boucle principale et du programme...")

conn.close()
