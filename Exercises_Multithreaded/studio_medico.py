from multiprocessing.connection import wait
from random import randint
from threading import Thread, RLock, Condition
import queue
from time import sleep

class Waiting_Room():
    def __init__(self):
        self.receip= queue.Queue()
        self.visit= queue.Queue()
        self.priority_receip= queue.Queue()
        self.add_lock=RLock()
        self.get_lock=RLock()
        self.cond_1=Condition(self.get_lock)
        self.cond_2=Condition(self.get_lock)
    
    def add_patient(self, patient, type):
        with self.get_lock:
            if type==0:
                self.receip.put(patient)
                self.cond_1.notify()
            elif type==1:
                self.visit.put(patient)
                self.cond_2.notify()
            else:
                self.priority_receip.put(patient)
    
    def get_patient(self, type):
            if type==0:
                if self.receip.empty():
                    return False
                return self.receip.get()

            elif type==1:
                while self.visit.empty():
                    sleep(0.1)
                return self.visit.get()

            else:
                if self.priority_receip.empty():
                    return False
                return self.priority_receip.get()
                
                
class Patient(Thread):
    def __init__(self, name, room):
        super().__init__()
        self.id=name
        self.waiting_room_ref=room
        self.type= randint(0,1)

    def run(self):
        with self.waiting_room_ref.add_lock:
            self.waiting_room_ref.add_patient(self, self.type)

    
class Doctor(Thread):
    def __init__(self, room):
        super().__init__()
        self.waiting_room_ref= room

    def call(self):
        with self.waiting_room_ref.get_lock:
            while self.waiting_room_ref.visit.empty():
                self.waiting_room_ref.cond_2.wait()
            patient=self.waiting_room_ref.get_patient(1)
            print("Il dottore chiama il paziente %s" %(patient.name))
            
            sleep(0.2)

            n=randint(2,3)
            if n==2:
                self.waiting_room_ref.add_patient(patient, 2)

    def run(self):
        while True:
            self.call()

class Secretary(Thread):
    def __init__(self, room):
        super().__init__()
        self.waiting_room_ref=room

    def call_receip(self):
        pat=self.waiting_room_ref.get_patient(2)
        if not pat:
            pat=self.waiting_room_ref.get_patient(0)

        print("La segretaria chiama il paziente %s " %(pat.name))
        
    def run(self):
        while True:
            with self.waiting_room_ref.get_lock:
                while self.waiting_room_ref.receip.empty():
                    self.waiting_room_ref.cond_1.wait()
                self.call_receip()

w_room=Waiting_Room()

doc=Doctor(w_room)
sec=Secretary(w_room)
pats=[Patient(i, w_room) for i in range(50)]

doc.start()
sec.start()
for p in pats:
    p.start()

            

        

