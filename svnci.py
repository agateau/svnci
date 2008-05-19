#!/usr/bin/env python
from optparse import OptionParser
import subprocess

class ChangedFile(object):
    __slots__ = ['status', 'path', 'toBeCommitted']
    def __init__(self, status, path):
        self.status = status
        self.path = path
        self.toBeCommitted = False


def getModifiedFiles(selectedFiles = None):
    if not selectedFiles:
        selectedFiles = []
    output = subprocess.Popen(["svn", "status"], stdout=subprocess.PIPE).communicate()[0]
    lst = []
    for line in output.split("\n"):
        line = line.strip()
        if len(line) == 0:
            continue
        status, path = line.split(" ", 1)
        path = path.strip()
        changedFile = ChangedFile(status, path)
        changedFile.toBeCommitted = path in selectedFiles
        lst.append(changedFile)

    return lst


def printEntry(option, label):
    print "%s: %s" % (option, label)


def printModifiedFiles(lst):
    for pos, fl in enumerate(lst):
        if fl.toBeCommitted:
            flag = "X"
        else:
            flag = " "
        caption = "[%s] %s %s" % (flag, fl.status, fl.path)
        printEntry(str(pos + 1), caption)


def addMissingFiles(lst):
    newFilesLst = [x.path for x in lst if x.toBeCommitted and x.status == '?' ]
    if len(newFilesLst) > 0:
        cmd = ["svn", "add"]
        cmd.extend(newFilesLst)
        subprocess.call(cmd)
        return True
    else:
        return False


def doCommit(lst):
    cmd = ["svn", "commit"]
    cmd.extend(lst)
    subprocess.call(cmd)


def viewDiff(lst):
    cmd = ["svn", "diff"]
    cmd.extend(lst)

    pagerCmd = ["view", "-"]

    p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(pagerCmd, stdin=p1.stdout)
    p2.communicate()


def main():
    parser = OptionParser()

    # Add an option which takes an argument and is stored in options.filename.
    # 'metavar' is an example of argument and should match the text in 'help'.
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")

    # Add a boolean option stored in options.verbose.
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")

    (options, args) = parser.parse_args()

    lst = getModifiedFiles()

    while True:
        print "-" * 30
        printModifiedFiles(lst)
        printEntry("r", "Refresh")
        printEntry("c", "Commit")
        printEntry("d", "Diff")
        printEntry("q", "Quit")
        print
        option = raw_input("Select an option: ")

        toBeCommittedLst = [x.path for x in lst if x.toBeCommitted]

        if option == "q":
            return

        elif option == "c":
            addMissingFiles(lst)
            doCommit(toBeCommittedLst)
            lst = getModifiedFiles(toBeCommittedLst)

        elif option == "r":
            lst = getModifiedFiles(toBeCommittedLst)

        elif option == "d":
            if addMissingFiles(lst):
                lst = getModifiedFiles(toBeCommittedLst)
            viewDiff(toBeCommittedLst)

        elif option.isdigit():
            idx = int(option) - 1
            lst[idx].toBeCommitted = not lst[idx].toBeCommitted
        else:
            print "Unknown option '%s'" % option

        print


if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
