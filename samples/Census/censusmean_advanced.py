import numpy
import pickle

import logging
import gupt
from computedriver.computedriver import GuptComputeDriver
import time
import censusdatadriver

from outputwriter import write_results, report_results, csv_header, report_results_repeated, csv_header_aggregates

logger = logging.getLogger(__name__)

from censusmean import MeanComputer


def sleep_short():
    "wait for printing before continuing logger printing"
    time.sleep(0.05)


def run_nonprivate(outfile=None, outfile_aggregates=None):
    """
    create baseline result.
    if outfile is given, also initialize the CSV file with a header line.
    """
    reader = censusdatadriver.get_reader()
    runtime = gupt.GuptRunTime(MeanComputer, reader, epsilon=0)
    
    # Returns type <class 'gupt.GuptOutput'>. 
    # Cast to list, to make similar to runtime.start() 
    result_nonprivate = list(runtime.start_nonprivate())
    
    # artificial 2nd dimension, just for testing these routines:
    # result_nonprivate = result_nonprivate + result_nonprivate 
    
    if outfile:
        output=(result_nonprivate, [0]*len(result_nonprivate), 
                "", "result_nonprivate", 0, 0)
        write_results(csv_header(example_output=output), outfile=outfile)
        write_results(output, outfile=outfile)
        print result_nonprivate , " = result_nonprivate"
        sleep_short()
        
        if outfile_aggregates:
            output = [result_nonprivate] + list(output) # one more column-family
            header = csv_header_aggregates(example_output=output)
            write_results(header, outfile=outfile_aggregates)
    
    return result_nonprivate


def run_expt(epsilon, gamma, 
             result_nonprivate, outfile=None, 
             bl_from=1, bl_to=3, windsorized=True):
    """
    given parameters, run 1 to 6 experiments
    """
    
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
            for _ in range(2):
                run_expt(epsilon, gamma, result_nonprivate, outfile=outfile)
    
      
############

def analyze_results(results):  #, result_nonprivate):
    """
    mean and standard deviation
    """
    res_dimensions = zip(*results)
    mean, std = [], []
     
    for resdim in res_dimensions:
        mean.append ( numpy.average(resdim) )
        std.append  ( numpy.std(resdim) )

    return mean, std
        


def repeat_expt(epsilon, gamma,
                result_nonprivate, 
                repetitions=10,
                outfile_singles=None, outfile_aggregates=None, 
                data_blocker=1, windsorized=False):
    """
    repeat 10 times to be able to estimate standard deviation
    """
    
    
    blocker = gupt.GuptRunTime.get_data_blockers()[data_blocker-1]
    # 1 NaiveDataBlocker
    # 2 ResamplingDataBlockerConstantSize 
    # 3 ResamplingDataBlockerConstantBlocks

    if not windsorized:
        DP_mode="standard_DP"
    else:
        DP_mode="windsorized_DP"

    logger.info("Running %d repetitions with data_blocker=%s" % (repetitions, blocker))
    logger.info("epsilon=%s gamma=%s, in mode %s" % (epsilon, gamma, DP_mode))
    
    results, starttime = [], time.clock()
    
    # results = pickle.load( open( "res.pickle", "rb" ))
     
    
    for i in range(repetitions):

        # TODO: Perhaps they DO or DO NOT have to be recreated in each run?
        blocker = gupt.GuptRunTime.get_data_blockers()[data_blocker-1]
        reader = censusdatadriver.get_reader()
        runtime = gupt.GuptRunTime(MeanComputer, reader, epsilon, 
                                   blocker_name=blocker, blocker_args=gamma)
        # end TODO

        if not windsorized:
            res=runtime.start()
        else:
            res=runtime.start_windsorized()
            
        # artificial 2nd dimension, just for testing these routines:
        # res = res + res
            
        print report_results(res, result_nonprivate, DP_mode, blocker, 
                             epsilon, gamma, outfile_singles)
        sleep_short()
    
        results.append(res)

    # pickle.dump(results, open( "res.pickle", "wb" ) )
    
    
    duration = time.clock() - starttime
    logger.info("%d repetitions took %.2f seconds" % (repetitions, duration))
    
    mean, std = analyze_results(results) # , result_nonprivate)
    
    print report_results_repeated(mean, std, DP_mode, blocker,
                                  epsilon, gamma, repetitions,
                                  outfile=outfile_aggregates)
    
    

def run_expt_many_times(result_nonprivate, repetitions=10,
                        data_blocker=1, windsorized=False,
                        outfile_singles=None, outfile_aggregates=None):
    """
    scanning through many epsilon & gamma values.
    """
    for epsilon in numpy.arange(0.1, 2.2, 0.2):#(0.2, 10, 0.2):
        for gamma in range(1, 10, 1):  # (1, 7, 1):
            
            repeat_expt(epsilon, gamma,
                        data_blocker=data_blocker, windsorized=windsorized,
                        result_nonprivate=result_nonprivate,
                        repetitions=repetitions,
                        outfile_singles=outfile_singles, 
                        outfile_aggregates=outfile_aggregates)
      


if __name__ == '__main__':
    
    """
    outfile="census-experiment-output.csv"
    result_nonprivate = run_nonprivate(outfile=outfile)
    run_original_expt(result_nonprivate, outfile)
    """
    
    outfile_singles   ="census-experiment-repetitions_singles.csv"
    outfile_aggregates="census-experiment-repetitions_aggregates.csv"
    result_nonprivate = run_nonprivate(outfile=outfile_singles, 
                                       outfile_aggregates=outfile_aggregates)

    """
    repeat_expt(epsilon=2, gamma=2,
                result_nonprivate=result_nonprivate, 
                repetitions=10,
                outfile_singles=outfile_singles, 
                outfile_aggregates=outfile_aggregates, 
                data_blocker=1, windsorized=False)
    """
    
    run_expt_many_times(result_nonprivate, 
                        repetitions=50,
                        data_blocker=1, 
                        windsorized=False,
                        outfile_singles=outfile_singles, 
                        outfile_aggregates=outfile_aggregates)
    
    
