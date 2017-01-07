#!/usr/bin/env python

import sys
import scipy.stats

import Script

# Main

def usage(what=None):
    if what == None:
        sys.stderr.write("""dmaptools.py - Operate on methylation data.

Usage: dmaptools.py command arguments...

where command is one of: merge, avgmeth, histmeth, dmr

merge - report per-replicate methylation values at differentially methylated sites
avgmeth - report and compare genome-wide methylation levels in two sets of replicates
histmeth - compare % methylation rates in two sets of replicates
dmr - detect differentially methylated regions

Use `dmaptools.py -h command' to display usage for `command'.

""")
    elif what == 'merge':
        sys.stderr.write("""dmaptools.py - Operate on methylation data.

Usage: dmaptools.py merge mcompfile matfile1 matfile2 [outfile]

Merge methylation data from two "mat" files `matfile1' and `matfile2' at the sites
listed in `mcompfile', containing differentially-methylated C positions. Write
the results to standard output or to `outfile' if specified.

""")
    elif what == 'avgmeth':
        sys.stderr.write("""dmaptools.py - Operate on methylation data.

Usage: dmaptools.py avgmeth matfile1 matfile2 [outfile]

Compute the average global methylation rates for all replicates in `matfile1' and `matfile2'
and report them, then test the significance of the difference between the two groups using
a two-sample t-test. The output (written to standard output or to `outfile' if specified)
has the following format:

File1: (name of matfile1)
Replicates1: (number of replicates in matfile1)
MethRates1: (comma-separated average methylation value for each replicate in matfile1)
File2: (name of matfile2)
Replicates2: (number of replicates in matfile2)
MethRates2: (comma-separated average methylation value for each replicate in matfile2)
Tstatistics: (T statistics from t-test)
P-value: (P-value from t-test)
Significant: (Y or N indicating if P-value < 0.01)
""")
    elif what == 'histmeth':
        sys.stderr.write("""dmaptools.py - Operate on methylation data.

Usage: dmaptools.py avgmeth matfile1 matfile2 [outfile]

(more to come)

""")
    elif what == 'dmr':
        sys.stderr.write("""dmaptools.py - Operate on methylation data.

Usage: dmaptools.py dmr [options] testbed ctrlbed

This command compares two BED files containing methylation rates for two different conditions, 
(test and control respectively) and detects regions of differential methylation (DMRs). The 
genome is divided into consecutive windows of `winsize' nucleotides. A window is identified as 
a DMR if: it contains at least `minsites1' sites in the test dataset and `minsites2' sites in
the control dataset having coverage higher than `mincov'; if the difference between the conversion
rates in test and control is higher than `methdiff'; and if the P-value of this difference, 
computed using Fisher's exact test, is smaller than `pval'.

Consecutive DMRs will be joined if the are separated by not more than `gap' windows. Only DMRs 
with a differential methylation in the same direction (ie, both positive or both negative) will
be joined, unless the -a option is specified. When regions are joined, the differential methylation
value is the average of those of the joined regions (or the average of their absolute values if
-a was specified) and the P-value is the highest of those in the joined regions.

Options:

 -o outfile   | Write output to `outfile' instead of standard output.
 -w winsize   | Set window size (default: {}).
 -t minsites1 | Minimum number of sites from test in DMR (default: {}).
 -s minsites2 | Minimum number of sites from control in DMR (default: {}).
 -c mincov    | Minimum coverage of sites for -t and -s (default: {}).
 -d methdiff  | Minimum difference of methylation rates (default: {}).
 -p pval      | P-value threshold (default: {}).
 -g gap       | Maximum gap for DMR joining (default: {}).
 -a           | Allow joining of DMRs in different directions.

""".format(DMR.winsize, DMR.minsites1, DMR.minsites2, DMR.mincov, DMR.mincov, DMR.methdiff, DMR.pval, DMR.gap))
    else:
        P.usage()

P = Script.Script("dmaptools.py", version="1.0", usage=usage,
                  errors=[('NOCMD', 'Missing command', 'The first argument should be one of: merge, avgmeth, dmr.')])

# Utils

def readDelim(stream):
    l = stream.readline().rstrip("\r\n")
    if l == '':
        return None
    else:
        return l.split("\t")

# Merger

class Merger():
    mcompfile = None
    matfile1 = None
    matfile2 = None
    outfile = None

    def __init__(self, args):
        nfiles = 0
        for a in args:
            if nfiles == 0:
                mcompfile = P.isFile(a)
                nfiles += 1
            elif nfiles == 1:
                matfile1 = P.isFile(a)
                nfiles += 1
            elif nfiles == 2:
                matfile2 = P.isFile(a)
                nfiles += 1
            elif nfiles == 3:
                outfile = a
        if nfiles < 3:
            P.errmsg(P.NOFILE)

    def makeMatMap(self):
        hdr = []
        mmap = {}
        with open(self.matfile, "r") as f:
            line = readDelim(f)
            hdr = line[4:]
            p = f.tell()
            while True:
                line = readDelim(f)
                if line == None:
                    break
                key = line[0] + ":" + line[1]
                # print "{} -> {}".format(key, p)
                # raw_input()
                mmap[key] = p
                p = f.tell()
        return (hdr, mmap)

    def mergeMatFiles(self, out):
        """Merge the contents of `matfile1' and `matfile2' at all locations contained in `mcompfile'.
    Write results to `outfile'."""
        hdr1 = []
        hdr2 = []
        nhdr1 = 0
        nhdr2 = 0
        map1 = {}
        map2 = {}

        sys.stderr.write("Indexing sites in `{}'... ".format(self.matfile1))
        (hdr1, map1) = makeMatMap(self.matfile1)
        sys.stderr.write("done, {} sites found.\n".format(len(map1)))
        sys.stderr.write("Indexing sites in `{}'... ".format(self.matfile2))
        (hdr2, map2) = makeMatMap(self.matfile2)
        sys.stderr.write("done, {} sites found.\n".format(len(map2)))

        nhdr1 = len(hdr1)
        nhdr2 = len(hdr2)

        # print "Header lengths: {}, {}".format(nhdr1, nhdr2)
        out.write("Chrom\tPos\tC1:Avg\tC1:Stdev")
        for h in hdr1:
            out.write("\tC1:" + h)
        out.write("\tC2:Avg\tC2:Stdev")
        for h in hdr2:
            out.write("\tC2:" + h)
        out.write("\n")

        nwritten = 0
        sys.stderr.write("Writing data for sites in `{}'... ".format(self.mcompfile))
        with open(self.matfile1, "r") as m1:
            with open(self.matfile2, "r") as m2:
                with open(self.mcompfile, "r") as f:
                    f.readline()
                    for line in f:
                        line = line.split("\t")
                        key = line[0] + ":" + line[1]
                        if key in map1 and key in map2:
                            fp1 = map1[key]
                            m1.seek(fp1)
                            dl1 = m1.readline().rstrip("\r\n")
                            fp2 = map2[key]
                            m2.seek(fp2)
                            dl2 = readDelim(m2)
                            out.write(dl1 + "\t" + "\t".join(dl2[2:]) + "\n")
                            nwritten += 1
        sys.stderr.write("done, {} sites in output.\n".format(nwritten))
        return nwritten
    
    def run(self):
        if self.outfile:
            with open(self.outfile, "w") as out:
                self.mergeMatFiles(out)
        else:
            self.mergeMatFiles(sys.stdout)

### Averager
### This command reads two -mat files and computes the average methylation of each
### sample across both conditions. It then compares the two sets of averages using
### a two-sample t-test.

class Averager():
    matfile1 = None
    nreps1 = 0
    matfile2 = None
    nreps2 = 0
    outfile = None
    pval = 0.01

    def __init__(self, args):
        next = ""
        for a in args:
            if a in ['-p']:
                next = a
            elif next == '-p':
                self.pval = P.toFloat(a)
                next = ""
            if self.matfile1 == None:
                self.matfile1 = P.isFile(a)
            elif self.matfile2 == None:
                self.matfile2 = P.isFile(a)
            elif self.outfile == None:
                self.outfile = a

    def methAvg(self, filename):
        nrows = 0
        sys.stderr.write("Reading {}... ".format(filename))
        with open(filename, "r") as f:
            hdr = readDelim(f)
            nreps = len(hdr) - 4
            counts = [0]*nreps
            sums = [0]*nreps

            for line in f:
                nrows += 1
                fields = line.split("\t")
                for i in range(nreps):
                    d = fields[i+4]
                    if d != "NA":
                        v = float(d)
                        if v >= 0:
                            counts[i] += 1
                            sums[i] += v
        avgs = [ sums[i] / counts[i] for i in range(nreps) ]
        sys.stderr.write("{} rows.\n".format(nrows))
        return (nreps, avgs)

    def report(self, out, avgs1, avgs2):
        out.write("File1: " + self.matfile1 + "\n")
        out.write("Replicates1: " + str(self.nreps1) + "\n")
        out.write("MethRates1: " + ",".join([str(x) for x in avgs1]) + "\n")
        out.write("File2: " + self.matfile2 + "\n")
        out.write("Replicates2: " + str(self.nreps2) + "\n")
        out.write("MethRates2: " + ",".join([str(x) for x in avgs2]) + "\n")
        (tstat, pval) = scipy.stats.ttest_ind(avgs1, avgs2)
        out.write("Tstatistics: " + str(tstat) + "\n")
        out.write("P-value: " + str(pval) + "\n")
        out.write("Significant: " + ("Y" if pval <= self.pval else "N") + "\n")

    def run(self):
        (nreps, avgs1) = self.methAvg(self.matfile1)
        self.nreps1 = nreps
        (nreps, avgs2) = self.methAvg(self.matfile2)
        self.nreps2 = nreps
        if self.outfile:
            with open(self.outfile, "w") as out:
                self.report(out, avgs1, avgs2)
        else:
            self.report(sys.stdout, avgs1, avgs2)

### Histcomparer
### This command reads two -mat files and reports the fraction of sites in each bin of % methylation
### for each replicate in the two conditions. It then determines whether the fractions are significantly
### different in each bin.

class Histcomparer(Averager):

    def methHist(self, filename):
        nrows = 0
        sys.stderr.write("Reading {}... ".format(filename))
        with open(filename, "r") as f:
            hdr = f.readline().split("\t")
            nreps = len(hdr) - 4
            counts = [0]*nreps
            hist = [ [0]*nreps for i in range(10) ]

            for line in f:
                nrows += 1
                fields = line.split("\t")
                for i in range(nreps):
                    d = fields[i+4]
                    if d != "NA":
                        v = float(d)
                        if v >= 0:
                            bin = int(v*10)
                            if bin == 10:
                                bin = 9
                            counts[i] += 1
                            hist[bin][i] += 1
        # print hist
        # print counts
        fracs = [ [ 1.0*hist[b][i] / counts[i] for i in range(nreps) ] for b in range(10) ]
        sys.stderr.write("{} rows.\n".format(nrows))
        return (nreps, fracs)

    def report(self, out, fracs1, fracs2):
        out.write("#Bin\tPval\tSignificant\tAvg1\tAvg2\n")
        for b in range(10):
            label = "{}-{}%".format(b*10, (b+1)*10)
            row1 = fracs1[b]
            row2 = fracs2[b]
            (tstat, pval) = scipy.stats.ttest_ind(row1, row2)
            out.write("\t".join([label, str(pval), ("Y" if pval <= self.pval else "N"), str(sum(row1) / self.nreps1), str(sum(row2) / self.nreps2)]) + "\n")

    def run(self):
        (nreps, fracs1) = self.methHist(self.matfile1)
        self.nreps1 = nreps
        (nreps, fracs2) = self.methHist(self.matfile2)
        self.nreps2 = nreps
        if self.outfile:
            with open(self.outfile, "w") as out:
                self.report(out, fracs1, fracs2)
        else:
            self.report(sys.stdout, fracs1, fracs2)

### DMR

class BEDreader():
    filename = None
    stream   = None
    current  = None
    chrom    = ""
    pos      = 0

    def __init__(self, filename):
        self.filename = filename
        self.stream = open(self.filename, "r")
        self.readNext()

    def close(self):
        self.stream.close()

    def readNext(self):
        """Read one line from stream and store it in the `current' attribute. Also sets `chrom' 
and `pos' to its first and second elements."""
        if self.stream == None:
            return None
        data = readDelim(self.stream)
        if data == None:
            # print "File {} finished.".format(self.filename)
            self.stream.close()
            self.stream = None
            return None
        self.current = [int(data[4]), int(data[5])]
        self.chrom = data[0]
        self.pos   = int(data[1])
    
    def skipToChrom(self, chrom):
        """Read lines until finding one that starts with `chrom'."""
        # print "Skipping to chrom {} for {}".format(chrom, self.filename)
        while self.chrom != chrom:
            self.readNext()
            if self.stream == None:
                break

    def readUntil(self, chrom, limit):
        """Read lines until reaching one that is after `pos' or is on a different chromosome. Returns:
- None if the BED file is finished,
- The new chromosome, if different from chrom,
- The list of records read otherwise.
"""
        result = []
        if self.stream == None:
            return None
        if chrom != self.chrom:
            return self.chrom
        while True:
            if self.pos < limit:
                result.append(self.current)
                self.readNext()
                if self.stream == None:
                    break
                if chrom != self.chrom:
                    break
            else:
                break
        return result

class DMRwriter():
    out = None
    maxdist = 0                 # Maximum distance between DMRs for joining
    samedir = True              # If true, only DMRs in the same direction will be joined
    chrom = ""
    nd = 0
    growing = []
    
    def __init__(self, out, maxdist, samedir=True):
        self.out = out
        self.maxdist = maxdist
        self.samedir = samedir
        self.growing = []
        out.write("#Chrom\tStart\tEnd\tDiff\tPval\n")

    def writeDMR(self):
        """Write out the DMRs in `growing'."""
        if self.nd == 0:
            return
        elif self.nd == 1:
            self.out.write("{}\t{}\t{}\t{}\t{}\n".format(*self.growing[0]))
        else:
            totdiff = 0.0
            maxpval = 0.0
            for d in self.growing:
                end = d[2]
                if self.samedir:
                    totdiff += d[3]
                else:
                    totdiff += abs(d[3])
                maxpval = max(maxpval, d[4])
            self.out.write("{}\t{}\t{}\t{}\t{}\n".format(self.growing[0][0], self.growing[0][1], end, totdiff/self.nd, maxpval))
        self.growing = []
        self.nd = 0

    def finish(self):
        self.writeDMR()

    def addDMR(self, data):
        if data[0] != self.chrom: # If chrom is different...
            self.writeDMR()       # write current DMRs and start over
            self.chrom = data[0]
        elif self.nd == 0:
            pass
        elif (data[1] - self.growing[-1][2]) <= self.maxdist: # these can be joined...
            if self.samedir and (data[3] * self.growing[-1][3]) < 0: # but not if they go in different directions and we want samedir
                self.writeDMR()
        else:
            self.writeDMR()       # can't join, write current DMRs and start over
        self.growing.append(data)
        self.nd += 1

class DMR():
    winsize = 100
    minsites1 = 0   # Minimum number of sites in test condition
    minsites2 = 4   # Minimum number of sites in control condition
    mincov = 4
    methdiff = 0.2
    pval = 0.01
    gap = 0         # Maximum number of non-DMR regions that can be joined
    samedir = True  # Only join DMRs in same direction?
    bedfile1 = None # BED file for test condition
    bedfile2 = None # BED file for control condition
    outfile = None
    growing = None              # buffer for DMRs that can potentially be joined

    def __init__(self, args):
        next = ""
        for a in args:
            if next == '-w':
                self.winsize = P.toInt(a)
                next = ""
            elif next == '-s':
                self.minsites2 = P.toInt(a)
                next = ""
            elif next == '-t':
                self.minsites1 = P.toInt(a)
                next = ""
            elif next == '-c':
                self.mincov = P.toInt(a)
                next = ""
            elif next == '-d':
                self.methdiff = P.toFloat(a)
                next = ""
            elif next == '-p':
                self.pval = P.toFloat(a)
                next = ""
            elif next == '-g':
                self.gap = P.toInt(a)
                next = ""
            elif next == '-o':
                self.outfile = a
                next = ""
            elif a in ['-w', '-s', '-t', '-c', '-d', '-p', '-o', '-g']:
                next = a
            elif a == '-a':
                self.samedir = False
            elif self.bedfile1 == None:
                self.bedfile1 = P.isFile(a)
            else:
                self.bedfile2 = P.isFile(a)
        if self.bedfile1 == None or self.bedfile2 == None:
            P.errmsg(P.NOFILE)

    def isDMR(self, data1, data2):
        """data1 = test, data2 = control."""
        ngood1 = 0
        totC1 = 0
        totT1 = 0
        ngood2 = 0
        totC2 = 0
        totT2 = 0

        for d in data1:
            if d[0] >= self.mincov:
                ngood1 += 1
            totC1 += d[1]
            totT1 += (d[0]-d[1])
        for d in data2:
            if d[0] >= self.mincov:
                ngood2 += 1
            totC2 += d[1]
            totT2 += (d[0]-d[1])

        # Do we have a sufficient number of sites?
        if ngood1 < self.minsites1 or ngood2 < self.minsites2:
            return None

        # Compute methdiff ratio. Is it above our threshold?
        ratio1 = 1.0 * totC1 / (totC1 + totT1)
        ratio2 = 1.0 * totC2 / (totC2 + totT2)
        diff = ratio1 - ratio2
        if abs(diff) >= self.methdiff:
            return None
        #print (diff, [[totC1, totT1], [totC2, totT2]])

        # Compute p-value
        (odds, pval) = scipy.stats.fisher_exact([[totC1, totT1], [totC2, totT2]])
        #print (odds, pval, diff, [[totC1, totT1], [totC2, totT2]])
        if pval <= self.pval:
            return (pval, diff)
        else:
            return None
        
    def findDMRs(self, out):
        DW = DMRwriter(out, self.gap*self.winsize, samedir=self.samedir)
        BR1 = BEDreader(self.bedfile1)
        BR2 = BEDreader(self.bedfile2)
        chrom = BR1.chrom       # assume that both BED file start with the same chrom - should check this!
        
        start = 0
        end = self.winsize
        nfound = 0
        totfound = 0

        while BR1.stream != None and BR2.stream != None:
            data1 = BR1.readUntil(chrom, end)
            data2 = BR2.readUntil(chrom, end)
            
            if isinstance(data1, basestring): # BR1 is at new chrom?
                sys.stderr.write("{}: {} DMRs\n".format(chrom, nfound))
                BR2.skipToChrom(data1)        # BR2 should join it
                totfound += nfound
                nfound = 0
                chrom = data1
                start = 0
                end = self.winsize

            elif isinstance(data2, basestring): # BR2 is at new chrom?
                sys.stderr.write("{}: {} DMRs\n".format(chrom, nfound))
                BR1.skipToChrom(data2)        # BR1 should join it
                totfound += nfound
                nfound = 0
                chrom = data2
                start = 0
                end = self.winsize
            
            else:               # Both are lists, OK
                if len(data1) > 0 and len(data2) > 0:
                    result = self.isDMR(data1, data2)
                    if result:
                        nfound += 1
                        (pval, diff) = result
                        DW.addDMR([chrom, start, end, diff, pval])

            # Move forward
            start += self.winsize                                                    
            end += self.winsize
        sys.stderr.write("{}: {} DMRs\n".format(chrom, nfound))
        sys.stderr.write("Total: {} DMRs\n".format(totfound))
        DW.finish()
        # BR1.close()
        # BR2.close()

    def run(self):
        if self.outfile:
            with open(self.outfile, "w") as out:
                self.findDMRs(out)
        else:
            self.findDMRs(sys.stdout)

### window-based DMR analysis:
### Params:
### window size
### min number of sites in window
### min coverage of each site in each sample
### methylation rate difference
### P-value
### number of non-DMRs for merging
### how to combine diffmeth in joined DMRs
###
### Output:
### chrom  start  end  diffmeth
###
### Additional: 
### average methylation level for each sample in each DMR

### T-test to compare methylation rates in replicates (from mat files)
### include methavg.py - DONE
### in histogram: compare percent in each bin for replicates of each condition - DONE

### in bedplotter: allow for larger window, using line graph instead of bar
### multiple samples overlayed on single graph

### check that mbed plotter works, generate figure 1A

### Re-run pipeline for genediffmeth in more regions - DONE
### Add links to mat files - DONE

if __name__ == "__main__":
    args = sys.argv[1:]
    nargs = len(args)
    if nargs == 0:
        P.errmsg(P.NOCMD)

    P.standardOpts(args)

    cmd = args[0]
    
    if cmd == 'merge':
        M = Merger(args[1:])
        M.run()
    elif cmd == 'avgmeth':
        M = Averager(args[1:])
        M.run()
    elif cmd == 'histmeth':
        M = Histcomparer(args[1:])
        M.run()
    elif cmd == 'dmr':
        M = DMR(args[1:])
        M.run()
    else:
        P.usage()
