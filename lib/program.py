
import sys
from os.path import dirname
from parser import program_parser

class Program:
    def __init__(self):
        self.eval_file(dirname(__file__)+'/prelude.pb')

    def eval_file(self,fname):
        self.fname = fname
        infile = open(fname) if fname != '-' else sys.stdin
        #TODO: figure out why parsing the file all at once fails
        for line in infile:
            self.eval_line(line)

    def eval_line(self,line):
        if not line.strip(): return
        res = program_parser.parseString(line).asList()
        if res == {}: return
        if len(res) == 1:
            return res[0]
        return res
