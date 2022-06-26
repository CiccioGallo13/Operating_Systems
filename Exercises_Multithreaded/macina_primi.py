from math import sqrt
from threading import Thread, RLock, Condition
N_THTREADS  = 6

class Barrier:
    def __init__(self, n):
        self.target=n
        self.arrived = 0
        self.lock = RLock()
        self.cond = Condition(self.lock)

    def wait(self):
        with self.lock:
            self.arrived+=1

            if self.arrived == self.target:
                self.cond.notify_all()
            while self.arrived < self.target:
                self.cond.wait()

class MacinaPrimi(Thread):
    
    def __init__(self, _b):
        super().__init__()
        self.min = 0
        self.max = 0
        self.totale = 0
        self.b = _b
    
    
    def contaPrimi (self, min, max):
        n_primes = 0
        for i in range(min, max):
            if self.isPrime(i):
                n_primes+=1
        return n_primes

    def isPrime(self, num):
        if num<=2:
            return True
        for i in range(2, int(sqrt(num)+1)):
            if num%i==0:
                return False
        return True
    
    def set_limits(self, _min, _max):
        self.min=_min
        self.max=_max

    def get_totale(self):
        return self.totale

    def run(self):
        self.totale = self.contaPrimi(self.min, self.max)
        self.b.wait()


def divider(min, max):
    tot = 0
    remains = 0
    barr = Barrier(N_THTREADS+1)
    nth=N_THTREADS
    if (max-min)%N_THTREADS!=0:
        remains= (max-min)%N_THTREADS

    primer = [MacinaPrimi(barr) for i in range(N_THTREADS)]

    n_part = (max-min)//N_THTREADS

    for i in range(1, N_THTREADS+1):
        if i==1:
            primer[i-1].set_limits(min, min+n_part+remains)
        else:
            primer[i-1].set_limits(min+ n_part*(i-1) + remains+1, min + n_part*i + remains)
    
    for i in range(N_THTREADS):
        primer[i].start()
    
    barr.wait()
    for i in range(nth):
        tot+=primer[i].get_totale()

    return tot

min = int(input("inserire il limite inferiore dell'intervallo di cui si vuole calcolare il numero di numeri primi -> "))

max = int(input("inserire il limite superiore dell'intervallo di cui si vuole calcolare il numero di numeri primi -> "))

print("Tra %d e %d ci sono %d numeri primi." %(min, max,divider(min, max)))