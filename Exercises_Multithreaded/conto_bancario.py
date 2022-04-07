from threading import Thread, RLock, Condition
from random import randint
from turtle import pos
from typing import List

class Transazione():
    def __init__(self, sorgente, destinazione, valore):
        super().__init__()
        self.source = sorgente
        self.destination= destinazione
        self.value = valore

class ContoBancario(Thread):
    def __init__(self, bank, n):
        super().__init__()
        self.lock= RLock()
        self.bank_ref=bank
        self.saldo = randint(0,1000)
        self.name = f"Conto {n}"
        self.pos=n
        self.n_transations=0
        self.past_transations= [None for i in range(50)]

    def run(self):
        while True:
            type= randint(0,2)
            if type==2:
                print("Il saldo del conto %s e' di %d." %(self.name, self.bank_ref.get_saldo(self.pos)))
            else:
                money=randint(1, 1000)
                other = self.pos
                while other == self.pos:
                    other = randint(0,499)
                if type == 0:
                    if self.bank_ref.transfer(self.pos, other, money):
                        print("Il %s ha trasferito %d€ al %s." %(self.name, money, self.bank_ref.conti[other].name))
                    else:
                        print("Non e' stato possibile trasferire dal %s %d€ al %s." %(self.name, money, self.bank_ref.conti[other].name))
                else:
                    if self.bank_ref.transfer(other, self.pos, money):
                        print("Il %s ha trasferito %d€ al %s." %(self.bank_ref.conti[other].name, money, self.name))
                    else:
                        print("Non e' stato possibile trasferire dal %s %d€ al %s." %(self.bank_ref.conti[other].name, money, self.name))





class Banca():
    def __init__(self):
        self.conti=[ContoBancario(self, i) for i in range(500)]

    def get_saldo(self, c):
        with self.conti[c].lock:
            return self.conti[c].saldo

    def transfer(self, A, B, N):
        with self.conti[A].lock:
            with self.conti[B].lock:

                if(self.conti[A].saldo< N):
                    return False
                self.conti[A].saldo-=N
                self.conti[A].past_transations[self.conti[A].n_transations%50]=Transazione(A,B,N)
                self.conti[A].n_transations+=1
                self.conti[B].saldo+=N
                self.conti[B].past_transations[self.conti[B].n_transations%50]=Transazione(A,B,N)
                self.conti[B].n_transations+=1
                return True

banca=Banca()
for i in range(100):
    banca.conti[i].start()