#!/usr/bin/env bash

PATH=/usr/local/bin/MagAGS:$PATH
cd /usr/local/bin/MagAGS

echo "Script /usr/local/bin/MagAGS/MagAGS.sh"
logger -s "Lancement de MagAGS.py"

printf "\n\n-----------------------------\nLancement de MagAGS.py - " >> MagAGS.out
date >> MagAGS.out
printf "\n\n-----------------------------\nLancement de MagAGS.py - " >> MagAGS.err
date >> MagAGS.err
printf "\n\n-----------------------------\nLancement de MagAGS.py - " >> MagAGS.log
date >> MagAGS.log
# Activation de l'environnement virtuel pour MagAGS
source "./MagAGS/bin/activate"

echo Appel du programme python MagAGS.py

if python -u ./MagAGS.py 1>> MagAGS.out 2>> MagAGS.err ; then
  fin=$?
  logger -s "Programme MagAGS.py terminé ok: ${fin}"
else
  logger -s "Programme MagAGS.py terminé en erreur: ${fin}"
fi

printf "Fin du script de lancement de MagAGS.py - " >> MagAGS.out
date >> MagAGS.out
printf "Fin du script de lancement de MagAGS.py - " >> MagAGS.err
date >> MagAGS.err
