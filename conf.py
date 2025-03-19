#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

def getconf(key):
    dic = {}
    value = ''
    try:
        f = open('MagAGS.conf')
    except Exception as err:
        print(f'err={str(err)}')
        return -1
    for l in f:
#        print('l=' + l)
        if l[0] != '#' and l[0] != ' ' and l[0] != '\n':
            l = l.strip('\n')
            s = l.split(',')
#            print('s[0]=' + s[0] + ' s[1]=' + s[1])
            try:
                dic[s[0]] = s[1]
            except Exception as err:
                print('bug dic[s[0]] = s[1]:' + 's=' + str(s) + ' ' + str(type(s)) + ' err=' + str(err))
                pass
            if s[0] == key:
                break # On a trouvé!
    f.close()
    try:
        value = dic[key]
    except Exception as err:
 #       print('Key error...' + key)
        return -1
    return value
    
def setconf(key, value):
    try:
        with open('monitormidnite.conf', "r") as f:
            t = f.readlines()
    except Exception as err:
        print('Bug open(r)... ' + str(err)) # Considérer créer le fichier de conf si il n'existe pas...
        return -1
    i=0
    while i < len(t)-1:
        if key in t[i]:
            t[i] = key + ',' + value + '\n'
            break # On a trouvé!
        i = i + 1

    try:
        with open('test.conf', "w") as f:
            f.writelines(t)
    except Exception as err:
        print('Bug open(w)... ' + str(err))
    print('t= ', t)

# Si appelé directement, offrir la possibilité de créer le fichier de configuration vide
# sous le nom passé comme paramètre. Si il existe, le signaler et ne rien faire. Préremplir
# avec une entête explicative du fonctionnement.
#
if __name__ == "__main__":
    pgm = os.path.basename(__file__)
    print("Voir contenu du fichier conf.py...")
    print(pgm)
    
    t = '# Fichier de configuration pour le programme ' + os.path.basename(__file__) + '.'
    t = t + '\n#'
    t = t + '\n# Le format est clef,paramètre'
    t = t + '\n#'
    t = t + '\n# Les commentaires sont permis'
    t = t + '\n#'
    t = t + '\n'
    
    pgm = pgm[0:pgm.find('.')]
    pgm = pgm + '.conf'
    
    try:
        with open(pgm, 'w') as f:
            print('write ' + pgm)
            f.writelines(t)
    except Exception as err:
        print('Bug création du fichier de conf: ' + str(err))
    
