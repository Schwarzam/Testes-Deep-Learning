from concurrent.futures import ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import threading
import inspect

import os
from datetime import datetime

import time
import tempfile

import psutil
from threading import Lock

global MarPool

class ControlThreads(ThreadPoolExecutor):
    def __init__(self, log_file = None, print_log = True, debug=False, max_workers=psutil.cpu_count(logical=True) - 2):
        ThreadPoolExecutor.__init__(self, max_workers)
        self.lock = Lock()
        
        self.tasks = {'default': []}
        self.log_file = log_file
        
        if self.log_file is not None:
            self.init_log()
        
        self.workers = max_workers
        self.print_log = print_log
        self.debug = debug
        
    def reconfigure(self, *args, **kwds):
        return super().__call__(*args, **kwds)

    def init_log(self):
        io = open(self.log_file, 'a')
        io.close()
        
    def submit(self, fn, *args, group = "default", **kwargs):
        future = super().submit(fn, *args, **kwargs)
        future.add_done_callback(worker_callbacks)
        if group not in self.tasks:
            self.tasks[group] = []
        self.tasks[group].append(future)

    def wait_process(self, group):
        self.MarP.wait_group_done(group)

    def get_queue_process(self, group = 'default'):
        return [i.done() for i in self.MarP.tasks[group]]
        
    def get_logs(self):
        f = open(self.log_file, 'r')
        return f.read()
    
    def get_queue(self, group = 'default'):
        return [i.done() for i in self.tasks[group]]
    
    def info(self, content, **kwargs):
        self.wlog(content, "[info]")
    def time(self, content):
        self.wlog(content, "[time]")
    def warn(self, content):
        self.wlog(content, "[warning]")
    def critical(self, content):
        self.wlog(content, "[critical]")
    def debug(self, content):
        if self.debug:
            self.wlog(content, "[debug]")
    
    def wlog(self, content, tipo="INFO", print_log = True):
        p = psutil.Process(os.getpid())

        if p.nice() < 10:
            p.nice(10)

        func = inspect.currentframe().f_back.f_back.f_code
        function = func.co_name
        filename = func.co_filename

        name = threading.current_thread().name

        log_message = f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  {tipo} - {os.path.basename(filename)} - {function}() - {str(content)}"
        # Print without skipping a line
        
        if print_log: 
            print(log_message, end="\n")
        
        if self.log_file is not None:
            with self.lock:
                io = open(self.log_file, 'a')
                io.write(log_message + "\n")
                io.close()

    def wait(self, group = "default"):
        if group not in self.tasks:
            return
        queue = [i.done() for i in self.tasks[group]]
        
        while False in queue:
            time.sleep(0.2)
            queue = [i.done() for i in self.tasks[group]]

    def clear_logs(self):
        io = open(self.log_file, 'w')
        io.close()

    def finishLog(self, filename):
        os.system(f'cp {self.log_file} {filename}')
        self.clear_logs()



def worker_callbacks(f):
    e = f.exception()

    if e is None:
        return

    trace = []
    tb = e.__traceback__
    while tb is not None:
        trace.append({
            "filename": tb.tb_frame.f_code.co_filename,
            "name": tb.tb_frame.f_code.co_name,
            "lineno": tb.tb_lineno
        })
        tb = tb.tb_next
    
    MarPool.critical(f"""{type(e).__name__}, {str(e)}, {trace}""")

control = ControlThreads(log_file=None, print_log = True, debug = True)