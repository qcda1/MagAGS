#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Program to monitor battery bank State Of Charge (SOC) and start/stop the generator in 
# accordance to a set minimum and maximum SOC.
#
# Written by Daniel Cote, Mars 2025
#

import logging
import sqlite3
import time
import datetime
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

# ===========Programme Principal=======================================================

#configure logging.
fmt = '%(asctime)s %(levelname)s %(lineno)s %(message)s'
logging.basicConfig(level=getconf('ll'), filename=getconf('lf'), format=fmt)
log = logging.getLogger('MagAGS')

log.setLevel(llevel(getconf('ll')))
log.info("Début du programme")
log.info("Log Level = %s", getconf('ll'))

# Backup des paramêtres de configuration
llevelb = ''

# Intervale de temps
interval = 60 # boucle aux 60 secondes

# Condition de la boucle sans fin. Si la valeur change, on sort de la boucle.
cmd = 'RUN'


# Connexion à la base de données
conn = sqlite3.connect("../monitormidnite/monitormidnite.db")
curs = conn.cursor()

# Objet relay
relay = Relay(idVendor=0x16c0, idProduct=0x05df)
# Turn all switches off
relay.state(0, on=False)

while cmd == 'RUN':
    start = time.time()
    log.debug("Bouclage... %s", str(start))
    # Valeurs des SOC min et max
    SOCmin = int(getconf('SOCsetpoints')[0:2])
    SOCmax = int(getconf('SOCsetpoints')[2:4])


    curs.execute("select dtm, soc from onem order by dtm desc limit 1")
    data = curs.fetchall()

    resp =manage_gen(data[0][1], SOCmin, SOCmax, relay)
#    print(f"dtm={data[0][0]}, SOCmin={SOCmin}, SOC={data[0][1]}, SOCmax={SOCmax}, resp = {resp}, currentstate={cvtstate(relay.state(1))}")

    if resp == "ON":
        relay.state(1, on=True)
        log.debug("Generator on")
    if resp == "OFF":
        relay.state(1, on=False)
        log.debug("Generator off")
    log.debug(f"dtm={data[0][0]}, SOCmin={SOCmin}, SOC={data[0][1]}, SOCmax={SOCmax}, resp = {resp}, currentstate={cvtstate(relay.state(1))}")
        
    duration = time.time() - start
    delay = interval - duration
    if delay > 0:
        try:
            time.sleep(delay)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt")
            cmd = 'STOP'
            break

log.info("Fin de la boucle principale")

conn.close()