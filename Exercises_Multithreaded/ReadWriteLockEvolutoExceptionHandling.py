#!/usr/bin/python3

from threading import RLock, Condition, Thread, current_thread
from time import sleep
from random import randint, random

#
# Funzione di stampa sincronizzata
#
plock = RLock()
def prints(s):
    plock.acquire()
    print(s)
    plock.release()

#
# Restituisce il Current THREAD ID (TID) di sistema formattato
#
def getThreadId():
    return f"{current_thread().ident:,d}"

#
# Errore WrongValue provocato se setDato imposta un valore negativo
#
class WrongValue(Exception):
    pass

class ReadWriteLockEvoluto:

    def __init__(self):
        self.dato = 0
        self.ceUnoScrittore = False
        self.numLettori = 0
        self.lockAusiliario = RLock()
        self.conditionAusiliaria = Condition(self.lockAusiliario)
        self.max_readers = 10
        self.enable = True

    def setReaders(self, max_readers : int):
        with self.lockAusiliario:
            #
            # Potrebbero esserci lettori in attesa che potrebbero sfruttare i nuovi posti.
            # Notifico questi eventuali lettori.
            #
            if max_readers > self.max_readers:
                self.conditionAusiliaria.notifyAll()
            self.max_readers = max_readers

    def enableWriters(self, enable : bool):
        with self.lockAusiliario:
            self.enable = enable
            #
            # Qualche scrittore che ha trovato il lock bloccato potrebbe 
            # beneficiare dello sblocco. Notifica in accordo a questo.
            #
            if enable:
                self.conditionAusiliaria.notifyAll()
                ##
                ##Possibile implementazione di una condition solo per gli scrittori, in modo da evitare
                ##di dover svegliare anche i lettori
                ##

    def acquireReadLock(self):
        with self.lockAusiliario:
            while self.ceUnoScrittore or self.numLettori >= self.max_readers:
                self.conditionAusiliaria.wait()
            self.numLettori += 1

    def releaseReadLock(self):
        with self.lockAusiliario:
            self.numLettori -= 1
            if self.numLettori < self.max_readers:
                self.conditionAusiliaria.notifyAll()
                ##
                ## In questo caso svegliare anche gli scrittori è utile, poichè
                ## il lettore potrebbe essere l'ultimo, quindi uno scrittore (sempre se la scrittura è abilitata)
                ## potrebbe prendere il lock e iniziare a scrivere
                ##

    def acquireWriteLock(self):
        with self.lockAusiliario:
            while self.ceUnoScrittore or self.numLettori > 0 or not self.enable:
                self.conditionAusiliaria.wait()
            self.ceUnoScrittore = True
            

    def releaseWriteLock(self):
        with self.lockAusiliario:
            self.conditionAusiliaria.notifyAll()
            self.ceUnoScrittore = False
            ##
            ## In questo caso svegliare tutti è la cosa migliore poichè sia uno scrittore che
            ## un lettore potrebbe iniziare a scrivere/leggere
            ##

    def getDato(self):
        return self.dato
    
    def setDato(self, i):
        #
        # Dato può essere solo positivo
        #
        if i < 0:
            raise WrongValue
        self.dato = i


class Scrittore(Thread):
    
    maxIterations = 1000

    def __init__(self, dc):
        super().__init__()
        self.dc = dc
        self.iterations = 0

    def run(self):
        while self.iterations < self.maxIterations:
            prints("Lo scrittore %s chiede di scrivere." % getThreadId())
            self.dc.acquireWriteLock()
            prints("Lo scrittore %s comincia a scrivere." % getThreadId() )
            sleep(random())
            v = random() * 10
            
            try:
                self.dc.setDato(v)
                prints(f"Lo scrittore {getThreadId()} ha scritto il valore {v:.2f}.")
                prints("Lo scrittore %s termina di scrivere." % getThreadId())
                self.dc.releaseWriteLock()
            except WrongValue:
                self.dc.releaseWriteLock()
                prints("Lo scrittore %s si arresta..(.Wrong value exception)" % getThreadId())
            ###
            ###Possibile context switch che potrebbe stampare un nuovo thread che legge o scrive
            ###prima che lo scrittore attuale abbia stampato di aver finito
            ###
            sleep(random() * 5)
            self.iterations += 1


class Lettore(Thread):
    maxIterations = 100

    def __init__(self, dc):
        super().__init__()
        self.dc = dc
        self.iterations = 0

    def run(self):
        while self.iterations < self.maxIterations:
            prints("Il lettore %s Chiede di leggere." % getThreadId())
            self.dc.acquireReadLock()
            prints("Il lettore %s Comincia a leggere." % getThreadId())
            sleep(random())
            prints("Il lettore %s legge." % self.dc.getDato())
            self.dc.releaseReadLock()
            ###
            ###Possibile context switch che potrebbe stampare un nuovo thread che legge o scrive
            ###prima che il lettore attuale abbia stampato di aver finito
            ###
            prints("Il lettore %s termina di leggere." % getThreadId())
            sleep(random() * 5)
            self.iterations += 1

#
# Codici ANSI per avere le scritte colorate su stampa console
#
redANSIcode = '\033[31m'
blueANSIcode = '\033[34m'
resetANSIcode = '\033[0m'
 
class TestaMetodi(Thread):
    maxIterations = 500

    def __init__(self, dc):
        super().__init__()
        self.dc = dc
        self.iterations = self.maxIterations

    def run(self):
        enable = True
        while self.iterations > 0:
            sleep(random() * 2)
            self.dc.enableWriters(enable)
            ###
            ###Possibile context switch che potrebbe stampare un nuovo thread che inizia a scrivere (nel caso di enable = True)
            ###prima che sia uscita a video la stampa degli scrittori abilitati
            ###
            prints(f"{redANSIcode}SCRITTORI ABILITATI: {enable:d}{resetANSIcode}")
            #
            # Inverte il valore di enable, così al prossimo giro imposta False se a questo
            # giro è stato impostato True. E viceversa
            #
            enable = not enable
            sleep(random() * 2)
            #
            # Imposta i readers a un valore random. 
            # Si noti che max_readers = 0 => nessun lettore
            # può accedere.
            #
            v = randint (0,10)
            self.dc.setReaders(v)
            ###
            ###Possibile context switch che potrebbe stampare un nuovo thread che inizia a leggere (nel caso di v > maxReaders)
            ###prima che sia uscita a video la stampa del numero di lettori aggiornata
            ###Oppure nel caso v<maxReaders un thread potrebbe essere messo in attesa prima della stampa col nuovo numero di lettori
            ###
            prints(f"{blueANSIcode}LETTORI ABILITATI: {v}{resetANSIcode}")

            self.iterations -= 1 



if __name__ == '__main__':
        dc = ReadWriteLockEvoluto()

        NUMS = 5
        NUML = 10
        scrittori = [Scrittore(dc) for i in range(NUMS)]
        lettori = [Lettore(dc) for i in range(NUML)]
        for s in scrittori:
            s.start()
        for l in lettori:
            l.start()
        #
        # Lancia una istanza di TestaMetodi anonima 
        #
        TestaMetodi(dc).start()
