'''
Created on 9 Aug 2017

@summary: functions for output reporting & saving to file
@author: andreas krueger
'''

import csv


# flatten a list of mixed lists & objects:  
flatten = lambda *n: (e for a in n
    for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))


def write_results(output, outfile):
    """
    write (flattened) output to CSV file:
    """
    with open(outfile, "a") as csvfile:
        writer=csv.writer(csvfile, 
                          delimiter=",", 
                          quotechar='"', quoting=csv.QUOTE_MINIMAL)
        row=list(flatten(output))
        writer.writerow(row)
        

def csv_header(example_output, datacolumns=["result", "abs_diff"], extracols=[]):
    """
    header for CSV file
    """
    header=[]
    numcols=len(datacolumns)
    for objects, name in zip(example_output[0:numcols], datacolumns):
        for i in range(len(objects)):
            header += [name+"%d"%i]
    header += ["DP_type", "blocker", "epsilon", "gamma"] + extracols
    return header
            
def csv_header_aggregates(example_output, 
                          datacolumns=["mean", "std", "stdrel"], 
                          extracols=["repetitions"]):
    return csv_header(example_output, datacolumns, extracols)
    

def report_results(result, result_nonprivate, DP_type, blocker, epsilon, gamma, outfile=None):
    """
    compare with nonprivate result, and tell all parameters.
    if outfile given, then also write to CSV file.
    """
    diff = [abs(i - j) for i, j in zip(result, result_nonprivate)]
    output = (result, diff, DP_type, blocker, epsilon, gamma)
    if outfile:
        write_results(output, outfile=outfile)
    output="%s diff %s with DP_type=%s blocker=%s epsilon=%s gamma=%s" % output
    return output

def report_results_repeated(mean, std, DP_type, blocker, epsilon, gamma, repetitions, outfile=None):
    """
    compare with nonprivate result, and tell all parameters.
    if outfile given, then also write to CSV file.
    """
    std_rel = [s/m for m, s in zip(mean, std)]
    output = (mean, std, std_rel, DP_type, blocker, epsilon, gamma, repetitions)
    if outfile:
        write_results(output, outfile=outfile)
    output="mean    %s\nstd     %s\nstd_rel %s\nat DP_type=%s blocker=%s epsilon=%s gamma=%s repetitions=%s" % output
    return output

