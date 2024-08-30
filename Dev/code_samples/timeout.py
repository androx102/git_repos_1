import time

import multiprocessing
from threading import Thread
import functools


def func_with_timeout(func_x,*args): #wrapper
    print("starting func")
    dummy_process = multiprocessing.Process(target=func_x,args=args)
    dummy_process.start()
    dummy_process.join(timeout=10)
    dummy_process.terminate()
    print("ended func")






def inner_test_func():
    for x in range(5):
        time.sleep(1)
        print(x)

        


if __name__ == "__main__":
    func_with_timeout(inner_test_func)
    time.sleep(20)