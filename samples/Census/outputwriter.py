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
        

def csv_header(example_output):
    """
    header for CSV file
    """
    header=[]
    for objects, name in zip(example_output[0:2], ["result", "abs_diff"]):
        for i in range(len(objects)):
            header += [name+"%d"%i]
    header += ["DP_type", "blocker", "epsilon", "gamma"]
    return header
            

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
