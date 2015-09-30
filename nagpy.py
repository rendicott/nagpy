
''' Small library of classes to generate Nagios return
code strings with system return codes. Also supports 
generating perfdata strings with field validation.

Uncomment example at bottom to test.'''


# define some custom exceptions.
class Ex_NagiosReturnCode_Initialize(Exception): pass
class Ex_NagiosReturnCode_GenReturnCodeString(Exception):
    def __init__(self,message=None):
        if not message:
            message = "Exception generating return code string from return code integer. Valid return codes are 0,1, and 2 for OK,WARNING, and CRITICAL respectively."
        Exception.__init__(self,message)

class Ex_NagiosReturnCode_GeneralException(Exception):
    def __init__(self,message=None):
        if not message:
            message = "General Exception. Unknown"
        Exception.__init__(self,message)

class Ex_PerfChunk_UnitValidation(Exception): pass
class Ex_PerfChunk_Initialize(Exception): pass

# this is the ultimate class that will generate the sys return code
class NagiosReturn(Exception):
    ''' Build and throw this exception to get Nagios to understand
    the output of your script. 

    This is an Exception designed to provide
    sys a return code from the execution of a Python
    Nagios script. Nagios expects every plugin to provide
    a return code (0,1,2) in order to determine ok/warn/crit.
    The message is what shows up as the output of a plugin in
    Nagios. 
    '''
    def __init__(self, message, code):
        self.message = message
        self.code = code

# make these and append them to NagiosReturnCode objects
class PerfChunk():
    ''' 
    stringname, value are required
    unit, warn, crit, minn, and maxx are optional
    
    Object for creating a perfdata chunk.
    Can iterate through these and tack them onto the
    end of the nagios string msg for single or multiple
    bits of perfdata. Note: This was written with 
    pnp4nagios in mind as a perfdata receiver. See 
    string format anatomy here: 
    https://docs.pnp4nagios.org/pnp-0.6/perfdata_format
    Essentially we're trying to build this:
    'label'=value[UOM];[warn];[crit];[min];[max]
    '''
    
    def __init__(self,stringname=None,value=None,unit=None,warn=None,crit=None,minn=None,maxx=None):
        ''' stringname, value are required
            unit, warn, crit, minn, and maxx are optional
        '''
        # perfdata chunks need to have a descriptor string name

        if stringname is None or value is None:
            raise Ex_PerfChunk_Initialize("Error initializing PerfChunk. " + 
                "Possibly wrong number of init arguments. " +
                "Minimum required: stringname and value. " + 
                "Optional: unit, warn, crit, min, max")
        else:
            self.stringname = stringname
            self.value = str(value)
            self.unit = self.set_unit(unit)
            if warn is None:
                warn = ''
            if crit is None:
                crit = ''
            if minn is None:
                minn = ''
            if maxx is None:
                maxx = ''
            self.warn = str(warn)
            self.crit = str(crit)
            self.min = str(minn)
            self.max = str(maxx)
            # we'll add support to flag a perfdata chunk as primary
            self.primary = False
    def genperfstring(self):
        ''' Returns a perfdata string based on the 
        properties assigned to the PerfChunk object.
        '''
        return("'%s'=%s%s;%s;%s;%s;%s" % (   self.stringname,
                                                self.value,
                                                self.unit,
                                                self.warn,
                                                self.crit,
                                                self.min,
                                                self.max,)
                )
    def dumpself(self):
        msg = "PerfChunk: \n\r"
        msg += "stringname = '%s' \n\r" % self.stringname 
        msg += "value = '%s' \n\r" % self.value
        msg += "unit = '%s' \n\r" % self.unit
        msg += "warn = '%s' \n\r" % self.warn
        msg += "crit = '%s' \n\r" % self.crit
        msg += "min = '%s' \n\r" % self.min
        msg += "max = '%s' \n\r" % self.max
        return(msg)
    def set_unit(self,unit):
        returnunit = ''
        # if no unit was specified, leave blank
        if not unit:
            returnunit = ''
        elif unit == 's' or unit == 'ms' or unit == 'us':
            # these are valid time units
            returnunit = unit
        elif unit == '%':
            # percentage is a valid unit
            returnunit = unit
        elif (  unit == 'B' or
                unit == 'MB' or
                unit == 'KB' or
                unit == 'GB' or
                unit == 'TB' ):
            # these are valid size units
            returnunit = unit
        elif unit == 'c':
            # this is a valid continuous counter unit
            returnunit = unit
        else:
            # raise a helpful Exception 
            raise Ex_PerfChunk_UnitValidation("Exception setting unit. Valid units are: " +
                        "(blank),s,ms,us,%,B,MB,KB,GB,TB,c")
        # so if all fails it will return a '' blank unit
        return returnunit

class NagiosReturnCode():
    ''' Designed to make it easy and safe to craft Nagios return 
    codes in Python. 
    Requires: returncode (0,1,2), msgstring
    Supports: handlers for multiple perfdata values etc.  

    Example of valid Nagios Plugin output is:
    DISK OK - free space: / 3326 MB (56%); | /=2643MB;5948;5958;0;5968
    / 15272 MB (77%);
    /boot 68 MB (69%);
    /home 69357 MB (27%);
    /var/log 819 MB (84%); | /boot=68MB;88;93;0;98
    /home=69357MB;253404;253409;0;253414 
    /var/log=818MB;970;975;0;980

    Full API description here:
    https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/3/en/pluginapi.html

    Desire is to eventually include crit/warn value checking within class.
    '''

    def __init__(self,returncode=None,msgstring=None):
        if returncode is None or not msgstring:
            raise Ex_NagiosReturnCode_Initialize("Exception: returncode and msgstring " +
                "are required to initialize NagiosReturnCode. Valid return codes are " +
                " integers: 0, 1, 2 which are OK, WARNING, and CRITICAL respectively.")
        try:
            int(returncode)
        except:
            raise Ex_NagiosReturnCode_Initialize("Exception trying to int(returncode). " + 
                "Valid return codes are " +
                " integers: 0, 1, 2 which are OK, WARNING, and CRITICAL respectively.")
        self.returnCode = self.validatereturncode(returncode)
        self.returnCodeString = self.genreturncodestring(returncode)
        self.messageString = msgstring
        self.perfChunkList = [] # list of PerfChunk objects
        ''' The perfChunkList will be serialized and tacked onto the overall Nagios
        return message. If no PerfChunks exist then no perfdata is returned.'''
        self.finalPerfString = ''
        self.additionalLines = [] # list of additional lines of LONGSERVICEOUTPUT
        self.finalAddLines = ''
        self.forceReturnCode = False # prevents override by another process
    def genperfchunkstrings(self):
        finalPerfString = ''
        #print(str(len(self.perfChunkList)))
        try:
            finalPerfString += '|'
            for chunk in self.perfChunkList:
                finalPerfString += ' %s' % chunk.genperfstring()
                #print(finalPerfString)
        except Exception as e:
            raise Ex_NagiosReturnCode_GeneralException(str(e))
            finalPerfString = ''
        return finalPerfString
    def genadditionallines(self):
        finalAddLines = ''
        try:
            for line in self.additionalLines:
                finalAddLines += '; \n %s' % line
        except Exception as e:
            raise Ex_NagiosReturnCode_GeneralException(str(e))
            finalAddLines = ''
        return finalAddLines
    def genreturncodestring(self,returncode):
        # if all else fails we'll default to CRITICAL
        returncodestring = 'CRITICAL'
        if returncode == 0:
            returncodestring = 'OK'
        elif returncode == 1:
            returncodestring = 'WARNING'
        elif returncode == 2:
            returncodestring = 'CRITICAL'
        else:
            raise Ex_NagiosReturnCode_GenReturnCodeString()
        return returncodestring
    def validatereturncode(self,returncode=None):
        # does simple integer validation on the returncode
        if returncode is None:
            returncode = 2 # default to CRITICAL
        else:
            try:
                int(returncode)
                if returncode > 2 or returncode < 0:
                    raise Ex_NagiosReturnCode_GenReturnCodeString()
                else:
                    return returncode
            except:
                raise Ex_NagiosReturnCode_GenReturnCodeString()
    def genreturncode(self):
        # re-evaluate if return code has changed
        self.validatereturncode(self.returnCode)
        self.returnCodeString = self.genreturncodestring(self.returnCode)
        self.finalPerfString = self.genperfchunkstrings()
        self.finalAddLines = self.genadditionallines()
        message = "%s %s %s ; %s" % (self.returnCodeString,self.messageString,self.finalAddLines,self.finalPerfString)
        #print(message)
        raise NagiosReturn(message,self.returnCode)

# EXAMPLE
'''
if __name__ == '__main__':
    import sys
    try:
        # build your perfdata chunk objects independently
        pd = PerfChunk(stringname='ddrive',value='2',unit='TB')
        pd1 = PerfChunk(stringname='cdrive',value='10',unit='GB')
        # build your nagios message and tell it to be warn,crit,ok, etc.
        nm = NagiosReturnCode(returncode=1,msgstring='disk space')
        # append your perfdata chunks to the NagiosReturnCode object.
        nm.perfChunkList.append(pd)
        nm.perfChunkList.append(pd1)
        nm.genreturncode() # will raise a 'NagiosReturn' exception 
    except NagiosReturn, e:
        print e.message
        sys.exit(e.code)
'''