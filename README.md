# nagpyrc
Python library that's handy for use in generating Nagios return code messages with perfdata. Import nagpyrc into your script and use the example at the bottom to easily generate Nagios return codes from your own scripts.

## Usage

```python
# EXAMPLE
if __name__ == '__main__':
    import sys
    from nagpyrc import NagiosReturn
    from nagpyrc import PerfChunk
    from nagpyrc import NagiosReturnCode
    
    # write some code that checks something
    # now use outputs from that to generate a NagiosReturnCode object.
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
```

### Another Example with Sample output
Snippet from main method
```python
def main(options):
    ''' The main() method. Program starts here.
    '''
    thisFunctionName = str(giveupthefunc())
    logging.debug("Options Parsed = " + str(options))
    ''' call the api '''
    # requests needs the timeout to be a float
    options.api_timeout = float(options.api_timeout)
    (   status_code,
        status_string,
        response_time) = call_api(  options.uri_base,
                                    options.uri_check,
                                    options.uri_auth,
                                    options.auth_username,
                                    options.auth_password,
                                    options.api_timeout
                                    )


    # build your perfdata chunk objects independently
    pd = PerfChunk(stringname='response_time',value=response_time,unit='s')
    # build your nagios message and tell it to be warn,crit,ok, etc.
    # we'll start with a default of 1 which is warning
    msgstring = "AdGateway API test status: " + str(status_code) + " " + str(status_string)
    nm = NagiosReturnCode(returncode=1,msgstring=msgstring)
    if status_code == 200:
        nm.returnCode = 0
    else:
        nm.returnCode = 1
    # append your perfdata chunks to the NagiosReturnCode object.
    nm.perfChunkList.append(pd)
    nm.genreturncode() # will raise a 'NagiosReturn' exception 
```
Output
```
OK AdGateway API test status: 200 OK  ; | 'response_time'=0.0913951396942s;;;;
```


## Future Enhancements
* need to add support for return code 3 'unknown'
