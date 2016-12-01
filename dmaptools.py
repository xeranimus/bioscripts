#!/usr/bin/env python

import sys

def makeMatMap(matfile):
    hdr = []
    mmap = {}
    with open(matfile, "r") as f:
        line = f.readline().rstrip("\r\n").split("\t")
        hdr = line[4:]
        p = f.tell()
        while True:
            line = f.readline()
            if line == '':
                break
            line = line.rstrip("\r\n").split("\t")
            key = line[0] + ":" + line[1]
            # print "{} -> {}".format(key, p)
            # raw_input()
            mmap[key] = p
            p = f.tell()
    return (hdr, mmap)

def mergeMatFiles(mcompfile, matfile1, matfile2, out):
    """Merge the contents of `matfile1' and `matfile2' at all locations contained in `mcompfile'.
Write results to `outfile'."""
    hdr1 = []
    hdr2 = []
    nhdr1 = 0
    nhdr2 = 0
    map1 = {}
    map2 = {}

    sys.stderr.write("Indexing sites in `{}'... ".format(matfile1))
    (hdr1, map1) = makeMatMap(matfile1)
    sys.stderr.write("done, {} sites found.\n".format(len(map1)))
    sys.stderr.write("Indexing sites in `{}'... ".format(matfile2))
    (hdr2, map2) = makeMatMap(matfile2)
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
    sys.stderr.write("Writing data for sites in `{}'... ".format(mcompfile))
    with open(matfile1, "r") as m1:
        with open(matfile2, "r") as m2:
            with open(mcompfile, "r") as f:
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
                        dl2 = m2.readline().rstrip("\r\n").split("\t")
                        out.write(dl1 + "\t" + "\t".join(dl2[2:]) + "\n")
                        nwritten += 1
    sys.stderr.write("done, {} sites in output.\n".format(nwritten))
    return nwritten
        
def usage():
    sys.stderr.write("""Usage: dmaptools.py mcompfile matfile1 matfile2 [outfile]

Merge methylation data from two "mat" files `matfile1' and `matfile2' at the sites
listed in `mcompfile', containing differentially-methylated C positions. Write
the results to standard output or to `outfile' if specified.
""")

if __name__ == "__main__":
    outstream = None
    if len(sys.argv) < 4:
        usage()
    elif len(sys.argv) == 4:
        mergeMatFiles(sys.argv[1], sys.argv[2], sys.argv[3], sys.stdout)
    elif len(sys.argv) == 5:
        with open(sys.argv[4], "w") as out:
            mergeMatFiles(sys.argv[1], sys.argv[2], sys.argv[3], out)
    else:
        usage()

