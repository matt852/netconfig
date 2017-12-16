#!/usr/bin/python

import re
import socket
import sys
import os
import errno
import hashlib
import logging
import netmiko_functions as nfn
from app import app
from datetime import datetime
from flask import session


class UserCredentials(object):
    """Stores interface authentication session results when searching for a client on the network."""

    def __init__(self, un, pw):
        """Initialization method."""
        self.un = un
        self.pw = pw

"""Global variables."""
# Credentials class variable.  Stores as creds.un and creds.pw for username and password
creds = UserCredentials('', '')
# Word to signify the user is done entering data.  Can be blank
stopword = "DONE"

"""Global logging settings."""
# Syslogging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Create a file handler
handler = logging.FileHandler(app.config['SYSLOGFILE'])
handler.setLevel(logging.INFO)
# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(handler)


def writeToLog(msg):
    """Write provided message to log file.

    Try/catch in case User isn't logged in, and Netconfig URL is access directly.
    """
    try:
        logger.info(session['USER'] + ' - ' + msg)
    except:
        logger.info('[unknown user] - ' + msg)


def debugScript(x):
    """For debugging purposes only."""
    print x
    sys.exit()


def debugErrorOut(num):
    """For debugging purposes only."""
    print "Error with script: #%s" % (num)
    print "Locals:"
    print locals()
    print "\nGlobals:"
    print globals()
    sys.exit()


def debugDict(d):
    """For debugging purposes only.

    Prints all contents of dictionary for debugging purposes.
    """
    for k, v in d.iteritems():
        print k, v


def setUserCredentials(username, password):
    """Return creds class with username and password in it."""
    creds.un = username
    creds.pw = password
    return creds


def replaceDoubleSpaces(x):
    """Return string with all double spaces removed, leaving only a single space."""
    while "  " in x:
        x = x.replace("  ", " ")
    return x


def replaceDoubleSpacesCommas(x):
    """Return string with all double spaces removed, leaving only a single comma."""
    x = x.replace("  ", ",,")
    while ",," in x:
        x = x.replace(",,", ",")
    return x


def replaceSpacesWithUnderscore(x):
    """Return string with all spaces replaced with an underscore."""
    x = x.replace(" ", "_")
    return x


def stripNewline(x):
    """Return string with newline character removed (carriage return)."""
    x = x.rstrip('\n')
    x = x.rstrip('\r')
    return x


def stripWhiteSpace(x):
    """Return string with all white space removed."""
    x = x.rstrip(' ')
    return x


def stripLastChar(x):
    """Strip last character from a string."""
    x = x[:-1]
    return x


def stripAllAfterChar(x, y):
    """Strip everything in string 'x' that comes after character 'y'."""
    x = x.split(y, 1)[0]
    return x


def splitOnNewline(x):
    """Split string on newline, returns as array."""
    x = x.split('\n')
    return x


def indexLookup(x):
    """Index lookup for determining Cisco IOS type.

    This needs to be cleaned up and standardized for multiple vendors.
    Returns index of -1 or -2, as IOS-XE/NX-OS has a trailing whitespace at the end of strings.
    This helps determine if a string came from IOS or IOS-XE/NX-OS.
    """
    if x:
        # Index of last variable in command output.  -1 if IOS
        return int('-1')
    else:
        # Index of last variable in command output.  -2 if IOS-XE or NX-OS
        return int('-2')


def file_len(fname):
    """Return number of items (lines) in a file as an integer."""
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def textBlock_len(x):
    """Return number of items (lines) in a given block of text."""
    i = 0
    for a in x:
        i += 1
    return i


def errorCheckEmptyIncResult(x):
    """Check if variable is empty or Incomplete.

    If variable is empty or contains an Incomplete entry, return True.
    Otherwise return False.
    """
    if not x or ("Inc" in x):
        return True
    else:
        return False


def isEmpty(x):
    """Check if variable is empty.

    If variable is empty, return True.
    Otherwise return False.
    """
    if not x:
        return True
    else:
        return False


def isSkipped(x):
    """Check if string contains 'skipped', for SSH sessions failing.

    If variable equals 'skipped', return True.
    Otherwise return False.
    """
    if x == 'skipped':
        return True
    else:
        return False


def containsSkipped(x):
    """Return if the word 'skipped' is in the provided string.

    Returns True if string contains the word "skipped".
    Returns False otherwise.
    """
    try:
        if "skipped" in str(x):
            return True
        return False
    except:
            return False


def isInt(x):
    """Check if value entered is a integer.

    Checks if x is an integer.
    Returns True if it is.
    Returns False if it isn't.
    """
    try:
        int(x)
        return True
    except ValueError:
        return False


def removeDictKey(d, key):
    """Remove key from dictionary."""
    r = dict(d)
    del r[key]
    return r


def getCurrentTime():
    """Get current timestamp for when starting a script."""
    currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return currentTime


def getScriptRunTime(startTime):
    """Return time elapsed between current time and provided time in 'startTime'."""
    endTime = getCurrentTime() - startTime
    return endTime


def makeDirectory(path):
    """Make directory, throw error if it doesn't work."""
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def printProgress(iteration, total, prefix='', suffix='', decimals=2, barLength=100):
    """Print iterations progress to terminal.

    Call in a loop to create terminal progress bar
    @params:
    iteration      - Required  : current iteration (Int)
        total      - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
    """
    filledLength = int(round(barLength * iteration / float(total)))
    percents = round(100.00 * (iteration / float(total)), decimals)
    bar = '#' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('%s [%s] %s%s %s  (%s/%s total)\r' % (prefix, bar, percents, '%', suffix, iteration, total))
    sys.stdout.flush()
    if iteration == total:
        print("\n")


def findLineInConfig(config, searchTerm):
    """Return line with specified text in provided config."""
    for item in config.split("\n"):
        if searchTerm in item:
            return item.strip()


def findLineAfterLineInConfig(config, startTerm, searchTerm):
    """Return the next line found following the specfied starting line.

    Example: Find the IP address (searchTerm) after interface Serial0/0/0 (startTerm).
    """
    t = False
    for item in config.split("\n"):
        if t:
            if searchTerm in item:
                return item.strip()
        if startTerm in item:
            t = True
    # If term isn't found, return empty value.
    # Function should return a value before this triggers.
    return ''


def readFromFile(inputFileName):
    """Read and return all contents from a file."""
    # Open file provided by user to import list of store numbers from
    fileRead = open(inputFileName, 'r')
    # Read each line of the file into array fileLines
    fileLines = fileRead.readlines()
    # Close this file once import is completed
    fileRead.close()
    # Return contents
    return fileLines


def writeCommandToFile(command, filename):
    """Write string/command to new file.  Doesn't append."""
    fileWrite = open(filename, 'wb')
    fileWrite.write(command)
    fileWrite.close()


def appendCommandToFile(command, filename):
    """Append string/command to new/existing file."""
    fileWrite = open(filename, 'ab')
    fileWrite.write(command)
    fileWrite.close()


def convertMacFormatDec2Col(oldMac):
    """Convert decimal notation MAC address into all uppercase colon delimited format.

    Example: inputting 1234.56ab.cdef returns 12:34:56:AB:CD:EF.
    """
    # Strip any newlines from string
    oldMac = stripNewline(oldMac)
    # Check var length.  If not equal to 14, return originally provided address.  Otherwise continue with conversion
    if len(oldMac) == 14:
        # Counter for 'for' loop
        i = 0
        # Set newMac var to null
        newMac = ''
        # Insert a colon after every 2nd character
        for char in oldMac:
            # Skip if character is a decimal
            if char != ".":
                # Append the character to the newMac string
                newMac += str(char)
                # Increment counter
                i += 1
            else:
                # Reset counter to 0
                i = 0
            # Check if remainder is 0, if so insert colon. Don't insert colon if at the end of the list
            if (i % 2 == 0) and (i > 0):
                newMac += ":"
        # Strip last character from string.  In this case, the colon at the very end
        newMac = stripLastChar(newMac)
        # Return converted MAC address in colon delimited format
        return newMac.upper()
    else:
        # Incorrect MAC format imported
        return oldMac


def convertMacFormatCol2Dec(oldMac):
    """Convert MAC address format with colons or hyphens to Cisco's decimal format.

    Converts uppercase or lowercase colon or hyphen delimited format MAC address into all lowercase decimal notation
    Example: inputting 12:34:56:AB:CD:EF returns 1234.56ab.cdef.
    """
    # Strip any newlines from string
    oldMac = stripNewline(oldMac)
    # Verify MAC address formatting is correct for colon or hyphen delimited format
    if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", oldMac.lower()):
        # Counter for 'for' loop
        i = 0
        # Set newMac var to null
        newMac = ''
        # Insert a decimal after every 4th character
        for char in oldMac:
            # Set skip variable if MAC address is colon delimited
            if macFormatType(oldMac) == 'c':
                skipVar = ':'
            # Set skip variable if MAC address is hyphen delimited
            elif macFormatType(oldMac) == 'h':
                skipVar = '-'

            if char != skipVar:
                # Append the character to the newMac string
                newMac += str(char)
                # Increment counter
                i += 1
            # Check if remainder is 0, if so insert colon. Don't insert colon if at the end of the list
            if (i % 4 == 0) and (i > 0):
                # Insert decimal into string every fourth character
                newMac += "."
                # Reset counter to 0
                i = 0
        # Strip last character from string.  In this case, the decimal at the very end
        newMac = stripLastChar(newMac)
        # Return converted MAC address in decimal delimited format
        return newMac.lower()
    else:
        # Incorrect MAC format imported
        return oldMac


def convertMacFormatText2Dec(oldMac):
    """Convert MAC address format from text to Cisco's decimal format.

    Converts uppercase or lowercase text only (no deliminations) formatted MAC address into all lowercase decimal notation
    Example: inputting 123456ABCDEF returns 1234.56ab.cdef
    """
    # Strip any newlines from string
    oldMac = stripNewline(oldMac)
    # Verify MAC address formatting is correct for colon or hyphen delimited format
    if re.match("[0-9a-f]{12}$", oldMac.lower()):
        # Counter for 'for' loop
        i = 0
        # Set newMac var to null
        newMac = ''
        # Insert a decimal after every 4th character
        for char in oldMac:
            # Append the character to the newMac string
            newMac += str(char)
            # Increment counter
            i += 1
            # Check if remainder is 0, if so insert colon. Don't insert colon if at the end of the list
            if (i % 4 == 0) and (i > 0):
                # Insert decimal into string every fourth character
                newMac += "."
                # Reset counter to 0
                i = 0
        # Strip last character from string.  In this case, the decimal at the very end
        newMac = stripLastChar(newMac)
        # Return converted MAC address in decimal delimited format
        return newMac.lower()
    else:
        # Incorrect MAC format imported
        return oldMac


def macFormatType(mac):
    """Determine MAC address format.

    Return 'c' for colon delimited format.
    Return 'h' for hypen delimted format.
    Return 'd' for decimal delimited format.
    Return 't' for text format (no delimiters).
    Return 'e' if no other matches.
    """
    # Regex expression for colon delimited format with 12 characters exactly
    if re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
        return 'c'
    # Regex expression for hypen delimited format with 12 characters exactly
    elif re.match("[0-9a-f]{2}([-])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
        return 'h'
    # Regex expression for decimal delimited format with 12 characters exactly
    elif re.match("[0-9a-f]{4}([.])[0-9a-f]{4}([.])[0-9a-f]{4}$", mac.lower()):
        return 'd'
    # Regex expression for text only format with no separators
    elif re.match("[0-9a-f]{12}$", mac.lower()):
        return 't'
    # Return 'e' if all checks above fail
    else:
        return 'e'


def md5(fname):
    """Determine MD5 checksum of file.

    Return MD5 checksum string.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def removeCharFromString(oldString, character):
    """Remove all instances of a provided character from a string, then returns string."""
    newString = oldString.replace(stripNewline(character), '')
    return newString


def getFileSize(imageFileFullPath):
    """Return size of file in bytes."""
    size = os.path.getsize(imageFileFullPath)
    return int(size)
'''
# Try to lookup switch hostname via reverse DNS
# If it fails, try to SSH in and pull the hostname via the switch config
# Otherwise returns IP address provided if it fails
def reverseDNSNetwork(host, creds):
    try:
        # Try host lookup via reverse DNS
        hostNameList = socket.gethostbyaddr(host)
    except socket.error, v:
        # If it fails, pull hostname from switch config
        hostNameList = sfn.runSSHCommand("show run | inc hostname", host, creds)
        try:
            # Try to parse hostname command from switch config to extra just the name
            # Split command output by a single space (no args defaults to split by whitespace)
            hostName = hostNameList.split()
        except:
            # If this doesn't work either, return as Unknown host
            return host
        # Return 2nd string from "show run | i hostname" command, which is just the name itself
        return hostName[1]
    # If reverse DNS lookup worked, continue from here
    # Split hostName by ' symbol
    hostNameFQDN = hostNameList[0].split("'")
    # Split hostNameFQDN by . symbol
    hostName = hostNameFQDN[0].split(".")
    #
    # Comment out the above line and return hostNameFQDN[0]
    # if you want to include the domain name in the hostname (FQDN)
    #
    # Return hostname of IP address from reverse DNS lookup
    return hostName[0]
'''


def reverseDNSEndpoint(host):
    """Try to lookup endpoint name via reverse DNS.

    Returns IP address provided if it fails.
    """
    try:
        # Try host lookup via reverse DNS
        hostNameList = socket.gethostbyaddr(host)
    except socket.error, v:
        # If it fails, return as a generic Endpoint
        return host
    # If reverse DNS lookup worked, continue from here
    # Split hostName by ' symbol
    hostNameFQDN = hostNameList[0].split("'")
    # Return hostname of IP address from reverse DNS lookup
    return hostNameFQDN[0]


def getCustomInput(typeOfInput, inputIsConfigCmds):
    """Get multiline input from user.

    Return all user input as a single variable/string.
    """
    text = ""
    print "\nTYPE OF INPUT NEEDED: %s" % (typeOfInput)
    print "\nPlease enter in this info one line at a time."
    if inputIsConfigCmds:
        print "Make sure to include exiting out of config t mode, and saving the config."
    print "Enter in the word 'DONE' in all caps when done.\n"
    # Loop until user enters in value saved as 'stopword'
    while True:
        # Store each user inputted line to variable 'line'
        line = raw_input()
        # If user input ('line' var) equals 'stopword', break loop
        if line.strip() == stopword:
            break
            # Otherwise, append line to end of all previous lines with a carriage return
        text += "%s\n" % line
    print "\n"
    # Split 'text' variable into list split by newlines
    text = text.splitlines()
    # Return all user input as a single variable/string
    return text


def md5VerifyOnDeviceWithSession(command, child):
    """Return true if verification succeeds, otherwise return false."""
    md5VerifyResult = nfn.runSSHCommandInSession(command, child)

    # Run for each line retreived from the md5 verification output
    for result in md5VerifyResult.split("\n"):
        # Reduce all spacing to just a single space per section
        result = replaceDoubleSpaces(result)

        # Split string by spaces.  We are looking for the 4th field
        resultList = result.split(" ")

        # If first word in string is 'Verified', then it worked
        if resultList[0] == "Verified":
            return True
        # If first word in string is '%Error' and second word is 'verifying', it failed
        elif resultList[0] == "%Error" and resultList[1] == "verifying":
            return False
        # Continue loop until one of the two above triggers
        else:
            continue
