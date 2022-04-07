import queue
from threading import RLock, Condition, Thread
from time import sleep

MAX_CAR=30
class Bridge:
    def __init__(self):
        self.dir_mode=0
        self.CAPACITY = 20
        self.car_queue_sea= []
        self.car_queue_mt= []
        self.on_bridge = queue.Queue(self.CAPACITY)
        self.lock= RLock()
        self.cond=Condition(self.lock)
        self.consecutive_sea=0
        self.consecutive_mt=0

    def check_cap(self):
            if self.on_bridge.full():
                return False
            return True

    def my_turn(self, turist):
        if turist.type<60:
           # print(turist.type, self.car_queue_sea[0].type)
            if self.car_queue_sea[0]==turist:
                return True
            return False
        else:
           # print(turist.type, self.car_queue_mt[0].type)
            if self.car_queue_mt[0]==turist:
                return True
            return False
        

class Turist(Thread):
    def __init__(self, _type, _bridge):
        super().__init__()
        self.type = _type
        self.bridge_ref= _bridge

    def check_turn(self):
        pass

    def put_on_queue(self):
        pass
    
    def run(self):
        self.check_turn()

class Turist_sea(Turist):
    def __init__(self, _t, _b):
        super().__init__(_t, _b)

    def put_on_queue(self):
        self.bridge_ref.car_queue_sea.append(self)

    def check_turn(self):
        with self.bridge_ref.lock:
            self.put_on_queue()
            print("Il turista %d si e' messo in coda" %(self.type))
            
            while not self.bridge_ref.my_turn(self) or not self.bridge_ref.check_cap()\
            or not self.bridge_ref.dir_mode==0:
                #print(not self.bridge_ref.my_turn(self), not self.bridge_ref.check_cap(), self.bridge_ref.dir_mode!=1)
                self.bridge_ref.cond.wait()
            self.bridge_ref.consecutive_mt=0
            self.bridge_ref.consecutive_sea+=1
            if(self.bridge_ref.consecutive_sea>MAX_CAR and not len(self.bridge_ref.car_queue_mt)==0):
                self.bridge_ref.dir_mode=1
            self.bridge_ref.on_bridge.put(self)
            print("Il turista %d sta attraversando il ponte..." %(self.type))
            #print(self.bridge_ref.car_queue_sea)
            self.bridge_ref.car_queue_sea.remove(self)
            #print(self.bridge_ref.car_queue_sea)
        sleep(0.1)
        with self.bridge_ref.lock:
            if len(self.bridge_ref.car_queue_sea)==0:
                self.bridge_ref.dir_mode=1
            print("Il turista %d ha attraverstato il ponte" %(self.type))
            self.bridge_ref.on_bridge.get()
            self.bridge_ref.cond.notify_all()

                
class Turist_mt(Turist):
    def __init__(self, _t, _b):
        super().__init__(_t, _b)

    def put_on_queue(self):
        self.bridge_ref.car_queue_mt.append(self)

    def check_turn(self):
        with self.bridge_ref.lock:
            self.put_on_queue()
            print("Il turista %d si e' messo in coda" %(self.type))
            while not self.bridge_ref.my_turn(self) or not self.bridge_ref.check_cap()\
            or not self.bridge_ref.dir_mode==1:
           #     print(not self.bridge_ref.my_turn(self), not self.bridge_ref.check_cap(), self.bridge_ref.dir_mode!=1)
                self.bridge_ref.cond.wait()
            self.bridge_ref.consecutive_mt+=1
            self.bridge_ref.consecutive_sea=0
            if(self.bridge_ref.consecutive_mt>MAX_CAR and not len(self.bridge_ref.car_queue_sea) ==0):
                self.bridge_ref.dir_mode=0
            self.bridge_ref.on_bridge.put(self)
            print("Il turista %d sta attraversando il ponte..." %(self.type))
            self.bridge_ref.car_queue_mt.remove(self)
        sleep(0.1)
        with self.bridge_ref.lock:
            if len(self.bridge_ref.car_queue_mt)==0:
                self.bridge_ref.dir_mode=0
            self.bridge_ref.on_bridge.get()
            print("Il turista %d ha attraverstato il ponte" %(self.type))
            self.bridge_ref.cond.notify_all()           

Ponte=Bridge()
sea=[Turist_sea(i, Ponte) for i in range(60)]
mt=[Turist_mt(i+60, Ponte) for i in range(60)]

for i in range(60):
    sea[i].start()
    mt[i].start()