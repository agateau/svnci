#!/usr/bin/env python
import os
from optparse import OptionParser
import subprocess

def findRepositoryRoot(arg):
    def isRepositoryRoot(x): return os.path.exists(os.path.join(x, ".bzr"))

    dir_ = os.path.abspath(arg)

    sep = os.path.sep
    if dir_[-1] == sep:
        dir_ = dir_[:-1]
    while not isRepositoryRoot(dir_):
        if dir_ == sep:
            raise Exception("Couldn't find repository in %s" % arg)
        dir_ = os.path.dirname(dir_)
    return dir_

class ChangedFile(object):
    __slots__ = ['status', 'path', 'toBeCommitted']
    def __init__(self, status, path):
        self.status = status
        self.path = path
        self.toBeCommitted = False


class WorkingCopyState(object):
    __slots__ = ['files', 'dirs']
    def __init__(self, dirs):
        self.dirs = dirs
        self.files = []


    def refresh(self):
        selectedFiles = self.filesToBeCommitted()
        cmd = ["bzr", "status", "--short"]
        cmd.extend(self.dirs)
        output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]

        self.files = []
        for line in output.split("\n"):
            line = line.strip()
            if len(line) == 0:
                continue
            status = line[:3]
            path = line[3:]
            status = status.strip()
            path = path.strip()
            changedFile = ChangedFile(status, path)
            changedFile.toBeCommitted = path in selectedFiles
            self.files.append(changedFile)


    def modifiedFiles(self):
        return [x.path for x in self.files]


    def filesToBeCommitted(self):
        return [x.path for x in self.files if x.toBeCommitted]


    def filesToAdd(self):
        return [x.path for x in self.files if x.toBeCommitted and x.status == '?']


def printEntry(option, label):
    print "%s: %s" % (option, label)


def printWorkingCopyState(state):
    for pos, fl in enumerate(state.files):
        if fl.toBeCommitted:
            flag = "X"
        else:
            flag = " "
        caption = "[%s] %s %s" % (flag, fl.status, fl.path)
        printEntry(str(pos + 1), caption)


"""
Takes a txt of the form "1 2 4-6"
returns 1,2,4,5,6
"""
def parseIndexList(txt):
    tokenList = txt.split(" ")
    indexSet = set()
    for token in tokenList:
        if "-" in token:
            start, end = token.split("-")
            start = int(start)
            end = int(end)
            indexSet.update( range(start, end + 1) )
        else:
            indexSet.add( int(token) )
    return indexSet


def bzrAdd(lst):
    cmd = ["bzr", "add"]
    cmd.extend(lst)
    subprocess.call(cmd)


def bzrCommit(lst):
    bugId = raw_input("Associated bug id, if any: ")
    cmd = ["bzr", "commit"]
    if bugId != "":
        cmd.append("--fixes")
        cmd.append("lp:%s" % bugId)
    cmd.extend(lst)
    subprocess.call(cmd)


def bzrPush():
    subprocess.call(["bzr", "push"])


def viewDiff(lst):
    cmd = ["bzr", "diff"]
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

    if len(args) == 0:
        dirs = [os.getcwd()]
    else:
        dirs = args

    root = findRepositoryRoot(os.getcwd())
    os.chdir(root)

    state = WorkingCopyState(dirs)
    state.refresh()

    while True:
        print "-" * 30
        printWorkingCopyState(state)
        printEntry("r", "Refresh")
        printEntry("c", "Commit")
        printEntry("d", "Diff")
        printEntry("p", "Push")
        printEntry("q", "Quit")
        print
        option = raw_input("Select an option: ")

        if option == "q":
            return

        elif option == "c":
            lst = state.filesToAdd()
            if len(lst) > 0:
                bzrAdd(lst)
            bzrCommit(state.filesToBeCommitted())
            state.refresh()

        elif option == "r":
            state.refresh()

        elif option == "d":
            lst = state.filesToAdd()
            if len(lst) > 0:
                bzrAdd(lst)
                state.refresh()
            viewDiff(state.filesToBeCommitted())

        elif option == "p":
            bzrPush()

        elif option[0].isdigit():
            idxList = parseIndexList(option)
            for idx in idxList:
                idx -= 1
                state.files[idx].toBeCommitted = not state.files[idx].toBeCommitted
        else:
            print "Unknown option '%s'" % option

        print


if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
