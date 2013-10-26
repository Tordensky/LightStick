from collections import defaultdict
import json


class Parser():
    def __init__(self):
        pass

    def countUniqueUsers(self, filename):
        recordList = self._logFileToList(filename)

        resultDict = defaultdict(int)
        for record in recordList:
            for user in record["history"]:
                resultDict[user] += 1

        print resultDict
        return len(resultDict)

    def _logFileToList(self, filename):
        logLines = []
        with open(filename, "r") as logfile:
            # READ HEADER
            print logfile.readline(),
            print logfile.readline(),
            print logfile.readline(),
            logfile.readline()

            # READ LOG DATA
            for line in logfile.readlines():
                logLines.append(json.loads(line))

        print "> %d number of records read from file" % len(logLines)
        return logLines

if __name__ == "__main__":
    parser = Parser()
    print parser.countUniqueUsers("insomniaDag2.log")