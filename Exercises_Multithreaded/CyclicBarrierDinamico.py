import math
import multiprocessing
from random import randint
from threading import Condition, Lock, Thread
import time

class Totale:
    def __init__(self):
        self.totale = 0
        self.lock = Lock()

    def getTotale(self):
        return self.totale

    def addToTotal(self, n):
        with self.lock:
            self.totale += n
       
class DistributoreNumeri:

    def __init__(self,min,max):
        self.min = min
        self.max = max
        self.numCorrente = min
        self.chunk = 15
        self.lock = Lock()

    def setQuantita(self, d):
        with self.lock:
            self.chunk = d
    '''
        Utilizzato dai macinatori per avere un numero da calcolare
    '''
    def getNextNumber(self):
        with self.lock:
            if self.numCorrente > self.max:
                return -1
            num = self.numCorrente
            self.numCorrente += 1
            return num

    def getNextInterval(self):
        with self.lock:
            if self.numCorrente > self.max:
                return -1
            num = self.numCorrente
            if num + self.chunk > self.max:
                self.numCorrente = self.max +1
                return range(num, self.max +1)
            self.numCorrente += self.chunk
            return range(num, num + self.chunk)

class Barrier:

    def __init__(self,n):

        self.soglia = n
        self.threadArrivati = 0
        self.lock = Lock()
        self.condition = Condition(self.lock)

    def wait(self):
        with self.lock:
            self.threadArrivati += 1

            if self.threadArrivati == self.soglia:
                self.condition.notifyAll()

            while self.threadArrivati < self.soglia:
                self.condition.wait()

'''
    Utilizzabile per testare se un singolo numero è primo
'''
def eprimo(n):
    if n <= 3:
        return True
    if n % 2 == 0:
        return False
    for i in range(3,int(math.sqrt(n)+1),2):
        if n % i == 0:
            return False
    return True

'''
    Utilizzabile per conteggiare un singolo intervallo di numeri primi
'''
def contaPrimiSequenziale(min,max):
    totale = 0
    for i in range(min,max+1):
        if eprimo(i):
            totale += 1
    return totale

class Macinatore(Thread):
    def __init__(self,d,b, t):
        super().__init__()
        self.min = min
        self.max = max
        self.totale = 0
        self.barrier = b
        self.distributore = d
        self.totHandler = t

    def getTotale(self):
        return self.totale
    
    def run(self):
        n = self.distributore.getNextInterval()
        quantiNeHoFatto = 0
        while(n != -1):
            rrr = randint(1,5000)
            if rrr == 14:
                rand = randint(1,150)
                self.distributore.setQuantita(rand)
                print("Sono il thread %s e ho settato il chunk  %d\n" %(self.getName, rand))
            for i in n:
                if eprimo(i):
                    self.totale += 1
                quantiNeHoFatto += 1
            n = self.distributore.getNextInterval()
        self.totHandler.addToTotal(self.totale)
        print(f"Il thread {self.getName()} ha finito e ha testato {quantiNeHoFatto} numeri")
        self.barrier.wait()

def contaPrimiMultiThread(min,max):

    nthread = multiprocessing.cpu_count()
    print(f"Trovato {nthread} processori" )
    ciucci = []
        
    b = Barrier(nthread+1)
    d = DistributoreNumeri(min,max)
    t = Totale()

    for i in range(nthread):
        ciucci.append(Macinatore( d, b, t ))
        ciucci[i].start()


    b.wait()

    totale = t.getTotale()
    return totale



min = 100000
max = 1000000
start = time.time()
nprimi = contaPrimiMultiThread(min,max)
elapsed = time.time() - start
print (f"Primi tra {min} e {max}: {nprimi}")
print (f"Tempo trascorso: {elapsed} secondi")


#68906