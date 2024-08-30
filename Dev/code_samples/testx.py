from threading import Thread
import time



class customthread(Thread):
    def __init__(self,func_to_run):
        super().__init__()
        self.test_flag = [True]
       # self.test_flag.append(True)
        self.func_to_run = func_to_run
    
    def run(self):
        while self.test_flag[0]:
            print(self.test_flag)
            self.func_to_run()

    def toggle_flag(self):
        self.test_flag[0] = False



class x():

    def func_with_timer(self):
        print("created thread")
        dummy_thread = customthread(self.inner_func)
        print("started thread")
        dummy_thread.start()
        dummy_thread.join(timeout=3)
        dummy_thread.toggle_flag()
        print("end")

    def inner_func(self):
        time.sleep(1)
        print("running")





if __name__ == '__main__':  
    xx = x()
    xx.func_with_timer() 
    pass
   # foo.mian_func()