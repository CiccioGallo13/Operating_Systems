from threading import Thread, RLock, Condition
from time import sleep

class Display(Thread):
    def __init__(self, _room):
        super().__init__()
        self.room_ref = _room
        self.doc = 'O'

    def show(self):
        if self.room_ref.doc:
            print('O')
        else:
            print("|%s|" %' '.join('*'*self.room_ref.visitors))

    def run(self):
        while self.room_ref.end>0:
            sleep(0.15)
            self.show()

class Room:
    def __init__(self, _name):
        self.name = _name
        self.doc = False
        self.visitors = 0
        self.day = True
        self.doc_lock = RLock()
        self.v_lock = RLock()
        self.doc_cond = Condition(self.doc_lock)
        self.v_cond = Condition(self.v_lock)
        self.end= 18

    def add_visitor(self):
        self.visitors+=1

    def remove_visitor(self):
        with self.v_lock:
            with self.doc_lock:
                self.visitors-=1
                self.v_cond.notify_all()
                if self.visitors==0:
                    self.doc_cond.notify_all()

    def doc_in(self):
        self.doc=True

    def doc_out(self):
        with self.v_lock:
            with self.doc_lock:
                self.doc = False
                self.doc_cond.notify_all()
                self.v_cond.notify_all()

    def finished(self):
        self.end-=1;


class Doctor(Thread):
    def __init__(self, _room):
        super().__init__()
        self.room_ref = _room

    def enter_room(self):
        with self.room_ref.doc_lock:
            while self.room_ref.visitors>0 or self.room_ref.doc:
                self.room_ref.doc_cond.wait()
            self.room_ref.doc_in()

    def leave_room(self):
        self.room_ref.doc_out()

    def visit(self):
        print("The doctor is visiting the patient %s..." %self.room_ref.name)
        sleep(0.3)
    
    def run(self):
        for i in range(20):
            sleep(0.15)
            self.enter_room()
            self.visit()
            self.leave_room()
        self.room_ref.finished()
    
    
class Visitor(Thread):
    def __init__(self, _room):
        super().__init__()
        self.room_ref = _room

    def enter_room(self):
        with self.room_ref.v_lock:
            while self.room_ref.visitors>5 or self.room_ref.doc:
                self.room_ref.v_cond.wait()
            self.room_ref.add_visitor()

    def leave_room(self):
        self.room_ref.remove_visitor()

    def run(self):
        for i in range(10):
            sleep(0.1)
            self.enter_room()
            sleep(0.2)
            self.leave_room()
        self.room_ref.finished()

room= Room('01')
docs= [Doctor(room) for i in range (3)]
vis = [Visitor(room) for i in range(15)]
disp = Display(room)

disp.start()
for i in range(15):
    if i<3:
        docs[i].start()
        vis[i].start()
    else:
        vis[i].start()