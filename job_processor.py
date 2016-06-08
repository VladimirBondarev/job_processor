# MIT License

# Copyright (c) 2016 Vladimir Bondarev

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
import time
import os
import subprocess as sub
from multiprocessing import Pool, Value, Lock


num_jobs_finished = Value('i', 0)
thread_lock = Lock()


def pool_initializer(*args):
    global thread_lock, num_jobs_finished
    thread_lock, num_jobs_finished = args


def job_worker(cmd):
    proc = sub.Popen(cmd, stdout=sub.PIPE, stderr=sub.PIPE, shell=True)
    output, errors = proc.communicate()

    with thread_lock:
        num_jobs_finished.value+=1
        sys.stdout.write('\r> Progress         : ' + str(num_jobs_finished.value))
        sys.stdout.flush()


def get_param_value(param_name, default_value):
    for arg in sys.argv:
        if arg.startswith('-' + param_name + '='):
            param = arg.split('=')
            param = param[len(param)-1]
            return param

    return default_value


if __name__ == '__main__':

    # Set number of threads used
    num_threads = int(get_param_value('threads', 7))

    # Set job file
    job_file = get_param_value('job_file', '')

    job_list = []

    # Process file lines into commands
    file_found = False
    if os.path.isfile(job_file):
        file_found = True
        with open(job_file) as file:
            for job in file:
                job = job.strip('\r\n\t')
                if len(job) > 0:
                    #print(job)
                    job_list.append(filter(None, job.split(' ')))

    num_jobs = len(job_list)
    if num_jobs == 0:
        if file_found:
            print('Job file' + job_file + 'is empty')
        else:
            if len(job_file) == 0:
                print('No job file specified, use command line argument -job_file="FILE_PATH"')
            else:
                print('Unable to open: ' + job_file)
        exit(1)

    sys.stdout.write('> File             : ' + job_file + '\n')
    sys.stdout.write('> Threads          : ' + str(num_threads) + '\n')
    sys.stdout.write('> Jobs             : ' + str(num_jobs) + '\n')
    sys.stdout.write('> Working directory: ' + os.getcwd() + '\n')
    sys.stdout.write('> Creating threads : ')
    sys.stdout.flush()

    # Create process pool
    pool = Pool(processes=num_threads, initializer=pool_initializer, initargs=(thread_lock, num_jobs_finished))

    sys.stdout.write('Ok\n')
    sys.stdout.write('> Progress         : ' + str(num_jobs_finished.value))
    sys.stdout.flush()

    time_start = time.time()

    # Execute jobs
    pool.map(job_worker, job_list)

    # Wait until all jobs are done
    pool.close()
    pool.join()

    sys.stdout.write('\n')
    sys.stdout.write('> Finished in      : ' + str(round(time.time() - time_start, 3)) + ' seconds')
    sys.stdout.write('\n')
