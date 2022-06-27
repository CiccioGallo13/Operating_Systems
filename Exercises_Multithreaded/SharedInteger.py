#!/usr/bin/env python
from threading import Thread,Condition,RLock,get_ident

class IllegalMonitorStateException(Exception):
    pass

'''
#
# Note sull'implementazione
#
#
# Lo shared integer presenta come unica difficoltà di implementazione il fatto che alcuni metodi (inc e setInTheFuture) modificano o leggono DUE sharedInteger
# CONTEMPORANEAMENTE.
#
# Per evitare deadlock e race condition insieme, si usano due classi molto utili:
#
# FriendlyLock: consente di fare acquire in contemporanea con un altro FriendlyLock 'amico', stando automaticamente attento a non creare deadlock
# usando il trucco dell'ordine lessicografico
#
# FriendlyCondition: una normale condition consente di andare in wait rilasciando solo il lock di appartenenza, ma non altri eventuali lock che si possiede;
# le FriendlyCondition consentono di fare wait() liberando tutti insieme un insieme di FriendlyLock. All'uscita della wait, tutti i friendlylock "amici" vengono riacquisiti.
#
# Grazie a FriendlyLock l'implementazione di inc diventa molto semplice, mentre invece FriendlyCondition ci aiuta a realizzare setInTheFuture in cui è necessario 
# attendere che cambi un certo intero per poi modificarne un secondo
#
'''
#
# Lock interno usato da tutti i friendlyLock e da tutte le friendlyCondition
# 
globalInternalLock = RLock()

class FriendlyLock:
#(Lock): non è stato possibile ereditare da Lock poichè non si possono ereditare le classi builtin

    #
    # Contatore statico che vale per tutte le istanze di classe. Usato per disciplinare l'ordine di acquire contemporanee
    #
    internalSerialCounter = 0

    def __init__(self):
        super(FriendlyLock, self).__init__()
        self.taken = False
        self.internalLock = globalInternalLock
        self.internalCondition = Condition(self.internalLock)
        #
        # Assegna un numero progressivo diverso a ogni FriendlyLock
        #
        FriendlyLock.internalSerialCounter += 1
        self.serial = FriendlyLock.internalSerialCounter
        #
        # ID del thread che attualmente possiede il lock
        #
        self.currentHolder = None
        #
        # Numero di volte che il possessore del lock ha fatto acquire(). Per ogni acquire() deve esserci una corrispondente release()
        #
        self.holds = 0

    def acquire(self, l  = None):
        # 
        # 	Se l != None, consente di prendere due FriendlyLock insieme nell'ordine anti-deadlock
        #
        if type(l) == FriendlyLock:
            if self.serial < l.serial:
                self.acquire()
                l.acquire()
            else:
                l.acquire()
                self.acquire()
        #
        # Non c'è l oppure l è del tipo sbagliato, simula il comportamento di una normale acquire
        #
        else:
            self.internalLock.acquire()
            while self.currentHolder != None and self.currentHolder != get_ident():
                    self.internalCondition.wait()
            self.currentHolder = get_ident()
            # 
            #  Conta eventuali lock multipli per garantire la rientranza
            # 
            self.holds += 1
            self.internalLock.release()

    # 
    #  se il parametro l è presente, rilascia due lock insieme. Notare che qui l'ordine di rilascio non è importante
    #             
    def release(self, l  = None):
        if type(l) == FriendlyLock:
            self.release()
            l.release()
        else:
            self.internalLock.acquire()
            try:
                if self.currentHolder == get_ident():
                    self.holds -= 1
                    if self.holds == 0:
                        self.currentHolder = None
                        self.internalCondition.notify()
                else:
                    # 
                    #  Non puoi rilasciare un lock che non appartiene al thread corrente (get_ident())
                    # 
                    raise IllegalMonitorStateException()
            finally:
                self.internalLock.release()

#
# Una friendlyCondition può avere più di un lock collegato, i quali vengono liberati tutti in caso di wait, e ripresi alla fine dell'attesa
#
class FriendlyCondition:
#(Condition): non è stato possibile ereditare da Condition poichè non si possono ereditare le classi builtin

    def __init__(self, l):
        super(FriendlyCondition, self).__init__()
        #
        # Insieme dei lock collegati
        #
        self.joinedLocks = list()
        #
        # Bisogna dichiarare almeno un lock collegati che viene subito messo tra i joinedLock
        #
        self.joinedLocks.append(l)
        #
        # Lock interno usato per disciplinare l'accesso alle variabili interne
        #
        self.internalLock = globalInternalLock
        #
        # Useremo delle condition interne per simulare wait e notify. Ogni thread in wait avrà una sua condition separata. Ne terremo traccia qui dentro
        #
        self.internalConditions = list()

#
# Aggiunge un lock all'insieme dei collegati
#
    def join(self, l):
        self.internalLock.acquire()
        self.joinedLocks.append(l)
        self.internalLock.release()

#
# Scollega un certo lock che prima era collegato
#
    def unjoin(self, l : FriendlyLock):
        self.internalLock.acquire()
        self.joinedLocks.remove(l)
        self.internalLock.release()

    #
    # Per implementare wait e notify, creo ogni volta una condition usa e getta che verrà usata per fare wait() e buttata alla prima notify().
    # 
    # Tutti i lock amici di questa Friendly condition vengo rilasciati temporaneamente e riacquisiti dopo la wait
    #
    def wait(self):
        self.internalLock.acquire()
        for i in self.joinedLocks:
            i.release()
        myCondition = Condition(self.internalLock)
        self.internalConditions.append(myCondition)
        # 
        #   Qui non uso un while di controllo. Come per le Condition native
        # 	Anchè la FriendlyCondition sarà soggetta agli spurious wake-up.
        #   Gli spurious wake-up andranno gestiti dal programmatore
        #   che usa le FriendlyCondition
        # 
        myCondition.wait()
        #
        # Riprendo tutti i lock collegati che avevo lasciato
        #
        for i in self.joinedLocks:
            i.acquire()
        self.internalLock.release()

    def notify(self):
        self.internalLock.acquire()
        toDelete = None
        for cond in self.internalConditions:
            # 
            #  Prendo solo la prima condition da notificare (questa non è notifyAll), faccio signal e poi faccio break;
            # 
            cond.notify()
            toDelete = cond
            break
        self.internalConditions.remove(toDelete)
        self.internalLock.release()

#
# In notifyAll devo considerare tutti i thread che potrebbero avere usato wait e sono in attesa. Per ciascuno ci sarà una condition dentro internalCondition.
# Faccio notify su tutte e pulisco il set di internalConditions perchè non mi servono più.
#
    def notifyAll(self):
        self.internalLock.acquire()
        for cond in self.internalConditions:
            cond.notify()
        self.internalConditions = list()
        self.internalLock.release()

    def notify(self):
        self.internalLock.acquire()
        toDelete = None
        for cond in self.internalConditions:
            # 
            #  Prendo solo la prima condition da notificare (questa non è notifyAll), faccio notify, cancello la condition e poi faccio break;
            # 
            cond.notify()
            toDelete = cond
            break
        self.internalConditions.remove(toDelete)
        self.internalLock.release()


#
# La classe Attesa mi serve per implementare gli SharedInteger e in particolare gestire tutti i thread che attendono il superamento di specifiche soglie.
# Ogni attesa corrisponde a una soglia fissata, e corrisponde a una Condition che è quella su cui fare notify per svegliare il thread corrispondente.
#
class Attesa:
    serialCounter = 0

    def __init__(self, i, c):
        #
        # Condition da notificare in futuro a superamento della soglia
        #
        self.c = c
        self.soglia = i
        Attesa.serialCounter += 1
        self.serial = Attesa.serialCounter

    # 
    #  Le attese sono ordinate dal valore piu' basso al più alto. 
    #  A parita' di valore vince l'elemento col seriale più basso.
    # 
    def __lt__(self, other):
        return self.soglia < other.soglia if self.soglia != other.soglia else self.serial < other.serial



class SharedInteger(object):

    def __init__(self):
        self.value = 0
        #
        # Non avendo a disposizione un SortedSet di serie in Python, invocheremo self.attese.sort() alla bisogna.
        # Così facendo self.attese sarà sempre ordinato.
        #
        self.attese = list()
        #
        # Qui sfrutteremo il FriendlyLock implementato sopra
        #
        self.lock = FriendlyLock()

    #
    # Fa notify su tutti gli eventuali thread in attesa di superamento soglia
    #
    def signalWaiters(self):
        for a in self.attese:
            if self.value > a.soglia:
                a.c.notifyAll()
            else:
                # 
                #  Siccome le attese sono ordinate dalla soglia più bassa alla più alta, mi fermo alla prima non superata da value. 
                #  Le soglie successive non saranno sicuramente superate.
                # 
                break

#
# NOTATE CHE il FriendlyLock somiglia a un Lock nativo come interfaccia ma NON implementa il costrutto "with:"
# 
    def get(self):
        self.lock.acquire()
        try:
            return self.value
        finally:
            self.lock.release()
#
# set, inc, oppure inc_int potrebbero far superare delle soglie su cui qualcuno aspetta
#
    def set(self, i):
        self.lock.acquire()
        self.value = i
        self.signalWaiters()
        self.lock.release()

    def inc(self, I):
        self.lock.acquire(I.lock)
        self.value += I.value
        self.signalWaiters()
        self.lock.release(I.lock)

    def inc_int(self, i : int):
        self.lock.acquire()
        self.value += i
        self.signalWaiters()
        self.lock.release()

    def waitForAtLeast(self, soglia):
        self.lock.acquire()
        try:
            cond = FriendlyCondition(self.lock)
            att = Attesa(soglia, cond)
            self.attese.append(att)
            self.attese = sorted(self.attese)
            while self.value < soglia:
                cond.wait()
            self.attese.remove(att)
            return self.value
        finally:
            self.lock.release()

    def setInTheFuture(self, I, soglia, valore):
        self.lock.acquire(I.lock)
        cond = FriendlyCondition(self.lock)
        cond.join(I.lock)
        att = Attesa(soglia, cond)
        # 
        #  Non dimentichiamo che sto aspettando il cambiamendo del valore di I, non di self
        #  Tuttavia non POSSO usare I.waitForAtLeast(soglia) poichè non potrei in contemporanea bloccare il lock su self.
        #
        #  Lo spezzone di codice
        #       I.waitForAtLeast(soglia)
        #       self.set(valore)
        #
        # Contiene una RACE CONDITION che non mi da la garanzia che I sia maggiore di soglia all'atto della self.set(valore)
        # 
        # Il problema si risolve usando un FriendlyLock insieme a una FriendlyCondition
        # 
        I.attese.append(att)
        self.attese = sorted(self.attese)
        while I.value < soglia:
            cond.wait()
        I.attese.remove(att)
        self.value = valore
        self.signalWaiters()
        self.lock.release(I.lock)

print("STARTING MAIN")
a = SharedInteger()
b = SharedInteger()
a.set(500)
b.set(1000)

class Thread1(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print(f"A ora vale: {a.get()}")
        print(f"sono il thread {get_ident()} e imposterò B a 5001 quando A supererà 999")
        b.setInTheFuture(a, 999, 5001)
        print(f"A è ora: {a.get()}")
        print(f"B è ora: {b.get()}")

class Thread2(Thread):

		
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        conta = 0;
        for i in range(0,500):
            a.inc_int(1);
            print("+", end='')
            conta += 1
            if conta > 50:
                print()
                conta = 0
                print(f"\nA vale ora: {a.get()}")

        print(f"Sono il Thread {get_ident()} e ora aspetterò che B sia 5000. In questo momento B è: {b.get()}")
        b.waitForAtLeast(5000)
        print(f"Aspettato B, che adesso vale: {b.get()}")


print("STARTING THREADS")
Thread1().start()
Thread2().start()
Thread2().start()

print("MAIN STARTED")
