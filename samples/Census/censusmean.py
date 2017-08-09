import logging
import gupt
from computedriver.computedriver import GuptComputeDriver
import time
import censusdatadriver

from outputwriter import write_results, report_results, csv_header

logger = logging.getLogger(__name__)

# Compute Provider Code
class MeanComputer(GuptComputeDriver):
    def initialize(self):
        self.total_age = 0.0
        self.num_records = 0
        self.total_income = 0.0

    def execute(self, record):
        if not record:
            return

        self.total_age += record[0]
        self.num_records += 1

    def finalize(self):
        try:
            return self.total_age / self.num_records
        except Exception, e:
            logger.exception(e)
            print self.total_age, self.num_records
            return 0,0

    def get_output_bounds(self, first_quartile=None, third_quartile=None):
        if not first_quartile or not third_quartile:
            # return [0.0, 0.0], [150.0, 500000.0]
            return [0.0], [150.0]
        return first_quartile, third_quartile
    
    
def sleep_short():
    "wait for printing before continuing logger printing"
    time.sleep(0.05)


def run_nonprivate(outfile=None):
    """
    create baseline result.
    if outfile is given, also initialize the CSV file with a header line.
    """
    reader = censusdatadriver.get_reader()
    runtime = gupt.GuptRunTime(MeanComputer, reader, epsilon=0)
    
    # returns type <class 'gupt.GuptOutput'>, so cast to list:
    result_nonprivate = list(runtime.start_nonprivate())    
    
    if outfile:
        output=(result_nonprivate, [0]*len(result_nonprivate), 
                "", "result_nonprivate", 0, 0)
        write_results(csv_header(example_output=output), outfile=outfile)
        write_results(output, outfile=outfile)
        print result_nonprivate , " = result_nonprivate"
        sleep_short()
    
    return result_nonprivate


def run_expt(epsilon, gamma, 
             result_nonprivate, outfile=None, 
             bl_from=1, bl_to=3, windsorized=True):
    
    blockers = gupt.GuptRunTime.get_data_blockers()[bl_from-1:bl_to]
    # print blockers; exit()
    # ['NaiveDataBlocker', 
    #  'ResamplingDataBlockerConstantSize', 
    #  'ResamplingDataBlockerConstantBlocks']

    for blocker in blockers:
        logger.info("running with data_blocker=%s" % blocker) 
        
        reader = censusdatadriver.get_reader()
        runtime = gupt.GuptRunTime(MeanComputer, reader, epsilon, blocker_name=blocker, blocker_args=gamma)
        res=runtime.start()
        print report_results(res, result_nonprivate, "standard_DP", blocker, epsilon, gamma, outfile)
        sleep_short()
        
        if not windsorized:
            continue
        
        reader = censusdatadriver.get_reader()
        runtime = gupt.GuptRunTime(MeanComputer, reader, epsilon, blocker_name=blocker, blocker_args=gamma)
        res=runtime.start_windsorized()
        print report_results(res, result_nonprivate, "windsorized_DP", blocker, epsilon, gamma, outfile)
        sleep_short()


def run_original_expt(result_nonprivate, outfile):
    """
    original experiment given in https://github.com/prashmohan/GUPT
    Runs 2 times with identical settings,
    each time standard_DP and windsorized_DP,
    while scanning through many epsilon & gamma values.
    """
    for epsilon in range(1, 10):
        for gamma in range(2, 5, 2):
            for index in range(2):
                run_expt(epsilon, gamma, result_nonprivate, outfile=outfile)
      

if __name__ == '__main__':
    outfile="census-experiment-output.csv"
    
    result_nonprivate = run_nonprivate(outfile=outfile)
    run_original_expt(result_nonprivate, outfile)
    
    
