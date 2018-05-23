#!/usr/bin/env python

# Input Oracle info report and spit out values based on the following formula
# Sizing:
# - DB       - 25 GB
# - Sapmnt   - 10 GB
# - Saparch  - 50 % of data files
# - Sapdata1 - Sum of CMO datafile size + 50%
# - Sapdata2 - Used for DBs > 1TB (Not Implemented!)

# Archive Logs are calculated with the following formula:
# if < 30 days of archive logs, use logtotal * 30 / numdays * 1.25
# If 30 days of archive logs, use logtotal * 1.15

import sys
import math
import argparse

try:
    from bottle import run, route, request
except ImportError as x:
    pass

class OraReport:
    """ Parse T-Systems Oracle info reports """
    def __init__(self):
        self.archiveStart = False
        self.archiveEnd = False
        self.dataFileStart = False
        self.dataFileEnd = False
        self.archiveCount = 0
        self.totalArchiveSize = 0
        self.dbData = {}

    def parseReportFile(self, reportFile):
        """ Parse reports from local files """
        try:
            f = open(reportFile, 'r')
        except IOError:
            print ("Error reading file")
            return 1

        fileInfo = reportFile.split("_")                        # Report name uses _ instead of spaces
        fileJunk = fileInfo[0].split('\\')
                                     # Remove path info (Windows)
        shortHost = fileJunk[-1].split(".")[0].upper()  # Get host shortname
        dbName = fileInfo[1]                         # Get db name
        return self.parseReport(f, shortHost, dbName)

    def parseReportWeb(self, reportFile):
        """ Parse reports from cherrypy file """
        fName = reportFile.files.filename
        # Report name uses _ instead of spaces
        host = fName.split("_")            
        # Get host shortname
        shortHost = host[0].split(".")[0].upper()  
        dbName = host[1]

        return self.parseReport(reportFile.files.data, shortHost, dbName)

    def parseReport(self, reportFile, hostName, dbName):

        self.dbData["Hostname"] = hostName
        self.dbData["DBName"] = dbName

        for line in reportFile:

            # Skip dashed lines
            if "----" in line:
                continue

            # Marks the entry point to the Archive log section
            if "ARCHIVE LOG" in line:
                self.archiveStart = True
                continue

            # We're in the middle of the archive section some where
            if self.archiveStart and not self.archiveEnd and len(line) > 5:
                if line[0].isdigit():       # Skip the Archive header line
                    self.archiveCount += 1  # Count the number of days we have archive logs
                    continue

            # We're at the end of the Archive section
            if line.startswith("sum") and self.archiveStart and not self.archiveEnd:
                self.archiveEnd = True
                if self.archiveCount < 30:  # Add 25% since we dont have a full months logs
                    tmpSize = int(line.split()[1].replace(",", ""))
                    totalArchiveSize = tmpSize * 30 / self.archiveCount * 1.25

                else:                   # Otherwise add 15%
                    totalArchiveSize = int(
                        line.split()[1].replace(",", "")) * 1.15
                continue

            # Enter into section with data file sizes
            if "TABLESPACES AND DATABASE SIZE" in line:
                self.dataFileStart = True
                continue

            # Inside data file section
            if self.dataFileStart and not self.dataFileEnd:
                if line.startswith("sum"):  # We only want the last line
                    data = line.split()
                    self.dataFileEnd = True

                    # Take the 3rd value and remove commas, multiple times 1.073 to get GB value from GiB
                    self.dbData["dbSize"] = int(data[2].replace(",", ""))
                    self.dbData["dbSize"] = int(math.ceil(self.dbData["dbSize"] * 1.073741824))

        self.dbData["DB"] = 25000                               # 25 GB
        self.dbData["SapMnt"] = 10000                           # 10 GB
        self.dbData["SapArch"] = int(math.ceil(self.dbData["dbSize"] / 2))    # Saparch - 50 % of data files
        self.dbData["SapData1"] = int(self.dbData["dbSize"] * 1.5)   # Sapdata1 - Sum of CMO datafile size + 50%
        self.dbData["Archive"] = int(totalArchiveSize)              # Multiply space * 30 days and add 15% to Archive size
        self.dbData["TotalSize"] = self.dbData["DB"] + self.dbData["SapMnt"] + self.dbData["SapArch"] + self.dbData["SapData1"] + self.dbData["Archive"]
        self.dbData["ArchiveCount"] = self.archiveCount

        return self.dbData

    def printReport(self, dbdata):

        # Print results
        print("Sizing results for DB instance {0} on host {1}").format(
            dbdata["DBName"], dbdata["Hostname"])
        print("{0:17} {1:12} {2:10}").format("MountPoint", "MB", "GB")
        print("-") * 35
        print("{0:12} {1:10} {2:10}").format("DB SW", dbdata["DB"], math.ceil(dbdata["DB"] / 1000))
        print("{0:12} {1:10} {2:10}").format("SapMnt", dbdata["SapMnt"], math.ceil(dbdata["SapMnt"] / 1000))
        print("{0:12} {1:10} {2:10}").format("SapArch", dbdata["SapArch"], math.ceil(dbdata["SapArch"] / 1000))
        print("{0:12} {1:10} {2:10}").format("SapData1", dbdata["SapData1"], math.ceil(dbdata["SapData1"] / 1000))
        print("{0} ({1}D) {2:9} {3:10}").format("Archive", dbdata["ArchiveCount"], dbdata["Archive"], math.ceil(dbdata["Archive"] / 1000))
        print("-") * 35
        print("{0:12} {1:10} {2:10}").format("Totals", dbdata["TotalSize"], math.ceil(dbdata["TotalSize"] / 1000))


class OraWeb:
    def index(self):
        return """
        <html><body>
            <h2>Upload Oracle info file</h2>
            <form action="/" method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile" /><br />
            <input type="submit" />
            </form>
            <a href="/exit">Quit</a>
        </body></html>
        """

    def upload(self):
        outData = """
            <html>
            <body>
            <table border="1">
                <tr>
                    <td colspan="3">Results for DB instance <b>%s</b> on host <b>%s</b></td>
                </tr>
                <tr>
                    <td>MountPoint</td>
                    <td>MB</td>
                    <td>GB</td>
                </tr>
                <tr>
                    <td>DB SW</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                <tr>
                    <td>SapMnt</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                <tr>
                    <td>SapArch</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                <tr>
                    <td>SapData1</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                <tr>
                    <td>SapData2</td>
                    <td></td>
                    <td></td>
                </tr>
                <tr>
                    <td>Archive (%s days)</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
                    <td>Totals</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>


                <a href="/exit">Quit</a>
                <a href="/">Start over</a>
            </body>
            </html>
            """

        report = OraReport()
        dbdata = report.parseReportWeb(request)

        mDbName = dbdata["DBName"]
        mHostName = dbdata["Hostname"]
        mSWSize = dbdata["DB"]
        mSapMnt = dbdata["SapMnt"]
        mSapArch = dbdata["SapArch"]
        mSapData1 = dbdata["SapData1"]
        mArchiveCount = dbdata["ArchiveCount"]
        mArchive = dbdata["Archive"]
        mTotal = dbdata["TotalSize"]

        return outData % (
            mDbName, mHostName, mSWSize, math.ceil(mSWSize / 1000),
            mSapMnt, math.ceil(
                mSapMnt / 1000), mSapArch, math.ceil(mSapArch / 1000),
            mSapData1, math.ceil(
                mSapData1 / 1000), mArchiveCount, mArchive,
            math.ceil(mArchive / 1000), mTotal, math.ceil(mTotal / 1000))

    def exit(self):
        raise SystemExit(0)
    exit.exposed = True


def main():
    # Setup argument parser, then run either cmdline or web
    parser = argparse.ArgumentParser(
        description='Process Oracle info reports.')
    parser.add_argument('-w', '--web', action='store_const', const=True, dest="runWeb", help="Start as webpage (requires cherrypy module)")
    parser.add_argument('-f', '--file', action='append', dest='inFiles',
                        default=[], help="Add list of files to run against")
    args = parser.parse_args()

    if args.runWeb:
        #from bottle import run, route, request
        import webbrowser
        o = OraWeb()

        route("/", method='GET')(o.index)
        route("/", method='POST')(o.upload)

        webbrowser.open("http://localhost:8080")
        run(host='localhost', port=8080, debug=True, reloader=True)

    elif args.inFiles:
        o = OraReport()
        o.printReport(o.parseReportFile(args.inFiles[0]))

if __name__ == '__main__':
    main()
