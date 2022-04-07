from secrets import choice
from symtable import Symbol
from tabnanny import check
from threading import Thread, RLock
import random
from time import sleep

class Display(Thread):
    def __init__(self, aisle):
        super().__init__()
        self.aisle_ref=aisle
    
    def print_s(self):
        print("|%s|" % ' '.join(self.aisle_ref.s))

    def run(self):
        while not self.aisle_ref.catch:
            self.aisle_ref.lock.acquire()
            self.print_s()
            self.aisle_ref.lock.release()
            sleep(0.1)
        self.print_s()


class Aisle:
    def __init__(self):
        self.dim = random.randint(5,20)
        self.s = [" "]*self.dim
        self.catch=False
        self.lock=RLock()


class Guinea_Pig(Thread):

    def __init__(self, aisle):
        super().__init__()
        self.speed = 1
        self.aisle_ref=aisle
        self.position= random.randint(0, aisle.dim-1)

    def check_borders(self):
        if self.position==self.aisle_ref.dim-1:
            return -1
        elif self.position== 0:
            return 1
        return 2

    def check_catched(self):
        if self.aisle_ref.s[self.position]!=" ":
            self.aisle_ref.catch= True

    def move(self, direction, symbol):
        self.aisle_ref.s[self.position]=" "
        self.position+=self.direction
        self.check_catched()
        if self.aisle_ref.catch:
            self.symbol='#'
        self.aisle_ref.s[self.position]= self.symbol

        
class Mouse(Guinea_Pig):

    def __init__(self, aisle):
        super().__init__(aisle)
        self.symbol="."
        self.direction = random.randint(-1,1)
    
    def run(self):
        while not self.aisle_ref.catch:
            self.aisle_ref.lock.acquire()
            if not self.aisle_ref.catch:
                if self.check_borders()==2:
                    self.direction=random.randint(-1,1)
                else:
                    self.direction=random.choice([self.check_borders(), 0])
                
                self.move(self.direction, self.symbol)
            self.aisle_ref.lock.release()
            sleep(0.1)
        

class Cat(Guinea_Pig):
    def __init__(self, aisle, mouse_index):
        super().__init__(aisle)
        self.symbol="*"
        self.mouse_index_ref= mouse_index
        self.direction=random.choice([-1,1])
    
    def run(self):
        while not self.aisle_ref.catch:
            self.aisle_ref.lock.acquire()
            if not self.aisle_ref.catch:
                if self.check_borders()!=2:
                    self.direction=self.check_borders()
                else:
                    if self.mouse_index_ref>self.position:
                        self.direction=1
                    elif self.mouse_index_ref<self.position:
                        self.direction=-1
            
                self.move(self.direction, self.symbol)
            self.aisle_ref.lock.release()
            sleep(0.1)


aisle=Aisle()
mouse=Mouse(aisle)
cat=Cat(aisle, mouse.position)
displayer=Display(aisle)

displayer.start()
mouse.start()
cat.start()
