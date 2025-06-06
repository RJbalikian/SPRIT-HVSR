import datetime
import functools
import inspect
import os
import pathlib
import subprocess
import sys
import traceback
import warnings
import zoneinfo

import numpy as np
from obspy.core.utcdatetime import UTCDateTime

try:  # For distribution
    from sprit import sprit_hvsr
except Exception: #For testing
    import sprit_hvsr
    pass

greek_chars = {'sigma': u'\u03C3', 'epsilon': u'\u03B5', 'teta': u'\u03B8'}
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}

def _assert_check(var, cond=None, var_type=None, error_message='Output not valid', verbose=False):
    if var_type is not None:
        assert isinstance(var, var_type), error_message
        if verbose:
            print(f"Output valid: {var} is instance of {var_type}", end='')
        
    if cond is not None:
        assert cond, error_message
        if verbose:
            if var_type is None:
                print('Output valid:', end=' ')
            else:
                print(' and ', end='')
            print(f"test condition is met.")
  

def _check_gui_requirements():
    #First, check requirements
    # Define a command that tries to open a window
    command = "python -c \"import tkinter; tkinter.Tk()\""

    # Run the command and get the exit code
    exit_code = os.system(command)
    
    # Check if tkinter gui could be created
    if exit_code == 0:
        #Tkinter 
        oktoproceed=True
    else:
        oktoproceed=False
        print("GUI window cannot be created.")

    return oktoproceed

    #if sys.platform == 'linux':
    #    # Check if qtwayland5 is installed
    #    output = subprocess.run(["dpkg", "-s", "qtwayland5"], capture_output=True, text=True)
    #    if "Status: install ok installed" in output.stdout:
    #        print("qtwayland5 is already installed")
    #    else:
    #        print("qtwayland5 is not installed")
    #        # Install qtwayland5
    #        os.system("sudo apt install qtwayland5")


#Get check mark
def _check_mark(incolor=False, interminal=False):
    """The default Windows terminal is not able to display the check mark character correctly.
       This function returns another displayable character if platform is Windows"""
    if incolor:
        try:
            check = _get_char(u'\u2705')
        except Exception:
            check = _get_char(u'\u2714')
    else:
        check = _get_char(u'\u2714')

    if sys.platform=='win32' and interminal:
        check = _get_char(u'\u039E')
    return check


#Converts filepaths to pathlib paths, if not already
def _checkifpath(filepath, sample_list='', verbose=False, raise_error=False):
    """Support function to check if a filepath is a pathlib.Path object and tries to convert if not

    Parameters
    ----------
    filepath : str or pathlib.Path, or anything
        Filepath to check. If not a valid filepath, will not convert and raises error

    Returns
    -------
    filepath : pathlib.Path
        pathlib.Path of filepath
    """
    if sample_list=='':
        sample_list = ['1', '2', '3', '4', '5', '6', 'sample', 'batch', 'sample', 'sample_batch']
        for s in range(1, 7):
            sample_list.append(f"sample{s}")
            sample_list.append(f"sample_{s}")

    # checks if the variable is any instance of pathlib
    if isinstance(filepath, pathlib.PurePath):
        pass
    elif str(filepath) in sample_list:
        pass
    else:
        try:
            filepath = pathlib.Path(filepath)
        except Exception:
            if verbose:
                warnings.warn('Filepath cannot be converted to pathlib path: {}'.format(filepath))
        if not filepath.exists():
            raise RuntimeError('File does not exist: {}'.format(filepath))

    return filepath


# Check to make the number of time-steps are the same for each channel
def _check_tsteps(hvsr_data):
    """Check time steps of PPSDS to make sure they are all the same length"""
    ppsds = hvsr_data['ppsds']
    tSteps = []
    for k in ppsds.keys():
        tSteps.append(np.array(ppsds[k]['psd_values']).shape[0])
    if len(set(tSteps)) <= 1:
        pass #This means all channels have same number of period_bin_centers
        minTStep=tSteps[0]
    else:
        print('There is a different number of time-steps used to calculate HVSR curves. \n This may result in computational errors. Trimming longest.')
        minTStep = min(tSteps)
    return minTStep


#Check the x-values for each channel, to make sure they are all the same length
def _check_xvalues(ppsds):
    """Check x_values of PPSDS to make sure they are all the same length"""
    xLengths = []
    for k in ppsds.keys():
        xLengths.append(len(ppsds[k]['period_bin_centers']))
    if len(set(xLengths)) <= 1:
        pass #This means all channels have same number of period_bin_centers
    else:
        print('X-values (periods or frequencies) do not have the same values. \n This may result in computational errors')
        #Do stuff to fix it?
    return ppsds


# Special helper function that checks the processing status at each stage of processing to help determine if any processing steps were skipped
def _check_processing_status(hvsr_data, start_time=datetime.datetime.now(), func_name='', verbose=False):
    """Internal function to check processing status, used primarily in the sprit.run() function to allow processing to continue if one site is bad.

    Parameters
    ----------
    hvsr_data : sprit.HVSRData
        Data being processed

    Returns
    -------
    sprit.HVSRData
        Data being processed, with updated the 'overall_status key of the attribute processing_status updated.
    """

    # Convert HVSRData to same format as HVSRBatch so same code works the same on both
    if isinstance(hvsr_data, sprit_hvsr.HVSRData):
        siteName = hvsr_data['site']
        hvsr_interim = {siteName: hvsr_data}
    else:
        hvsr_interim = hvsr_data
    
    # Check overall processing status on all (or only 1 if HVSRData) site(s)
    optional = ['remove_noise_status', 'remove_outlier_curves_status', 'calculate_azimuths_status', 'overall_status']
    for sitename in hvsr_interim.keys():
        statusOK = True
        for status_type, status_value in hvsr_interim[sitename]['processing_status'].items():
            if status_value is False and status_type.lower() not in optional:
                statusOK = False

        if statusOK:
            hvsr_interim[sitename]['processing_status']['overall_status'] = True
        else:
            hvsr_interim[sitename]['processing_status']['overall_status'] = False

    # Get back original data in HVSRData format, if that was the input
    if isinstance(hvsr_data, sprit_hvsr.HVSRData):
        hvsr_data = hvsr_interim[siteName]
    
    # Print how long it took to perform function
    if verbose:
        elapsed = (datetime.datetime.now()-start_time)
        print(f"\t\t{func_name} completed in  {str(elapsed)[:-3]}")

    return hvsr_data


# Formats time into desired output
def _format_time(inputDT, tzone='UTC'):
    """Private function to format time, used in other functions

    Formats input time to datetime objects in utc

    Parameters
    ----------
    inputDT : str or datetime obj 
        Input datetime. Can include date and time, just date (time inferred to be 00:00:00.00) or just time (if so, date is set as today)
    tzone   : str='utc' or int {'utc', 'local'} 
        Timezone of data entry. 
            If string and not utc, assumed to be timezone of computer running the process.
            If int, assumed to be offset from UTC (e.g., CST in the United States is -6; CDT in the United States is -5)

    Returns
    -------
    outputTimeObj : datetime object in UTC
        Output datetime.datetime object, now in UTC time.

    """
    # Initialize values
    year = 2000
    month = 1
    day = 1

    if tzone is None:
        tzone = 'UTC'

    # Parse whether inputDT has date or not
    if isinstance(inputDT, str):
        # tzone = 'America/Chicago'
        # Format string to datetime obj
        div = '-'
        timeDiv = 'T'
        if "/" in inputDT:
            div = '/'
            hasDate = True
        elif '-' in inputDT:
            div = '-'
            hasDate = True
        else:
            hasDate = False
            year = datetime.datetime.today().year
            month = datetime.datetime.today().month
            day = datetime.datetime.today().day

        if ':' in inputDT:
            hasTime = True
            if 'T' in inputDT:
                timeDiv = 'T'
            else:
                timeDiv = ' '
        else:
            hasTime = False

        if hasDate:
            # If first number is 4-dig year (assumes yyyy-dd-mm is not possible)
            if len(inputDT.split(div)[0]) > 2:
                year = inputDT.split(div)[0]
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[2].split(timeDiv)[0]

            # If last number is 4-dig year        
            elif len(inputDT.split(div)[2].split(timeDiv)[0]) > 2:
                #..and first number is day
                if int(inputDT.split(div)[0])>12:
                    #dateStr = '%d'+div+'%m'+div+'%Y'   
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    month = inputDT.split(div)[1]
                    day = inputDT.split(div)[0]
                #...and first number is month (like American style)                             
                else:
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    month = inputDT.split(div)[0]
                    day = inputDT.split(div)[1]     

            # Another way to catch if first number is (2-digit) year
            elif int(inputDT.split(div)[0]) > 31:
                #dateStr = '%y'+div+'%m'+div+'%d'
                year = inputDT.split(div)[0]
                #Assumes anything less than current year is from this century
                if year < datetime.datetime.today().year:
                    year = '20'+year
                else:#...and anything more than current year is from last century
                    year = '19'+year
                #assumes day will always come last in this instance, as above
                month = inputDT.split(div)[1]
                day = inputDT.split(div)[2].split(timeDiv)[0]

            # If last digit is (2 digit) year
            elif int(inputDT.split(div)[2].split(timeDiv)[0]) > 31:
                #...and first digit is day
                if int(inputDT.split(div)[0])>12:
                    #dateStr = '%d'+div+'%m'+div+'%y'       
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    if year < datetime.datetime.today().year:
                        year = '20'+year
                    else:
                        year = '19'+year
                    month = inputDT.split(div)[1]
                    day = inputDT.split(div)[0]                           
                else: #...and second digit is day
                    #dateStr = '%m'+div+'%d'+div+'%y'
                    year = inputDT.split(div)[2].split(timeDiv)[0]
                    if year < datetime.datetime.today().year:
                        year = '20'+year
                    else:
                        year = '19'+year
                    month = inputDT.split(div)[0]
                    day = inputDT.split(div)[1]                  

        hour = 0
        minute = 0
        sec = 0
        microS = 0
        if hasTime:
            if hasDate:
                timeStr = inputDT.split(timeDiv)[1]
            else:
                timeStr = inputDT
            
            if 'T' in timeStr:
                timeStr=timeStr.split('T')[1]
            elif ' ' in timeStr:
                timeStr=timeStr.split(' ')[1]

            timeStrList = timeStr.split(':')
            if len(timeStrList[0])>2:
                timeStrList[0] = timeStrList[0][-2:]
            elif int(timeStrList[0]) > 23:
                timeStrList[0] = timeStrList[0][-1:]
            
            if len(timeStrList) == 3:
                if '.' in timeStrList[2]:
                    microS = int(timeStrList[2].split('.')[1])
                    timeStrList[2] = timeStrList[2].split('.')[0]
            elif len(timeStrList) == 2:
                timeStrList.append('00')

            hour = int(timeStrList[0])
            minute = int(timeStrList[1])
            sec = int(timeStrList[2])

        outputTimeObj = datetime.datetime(year=int(year),month=int(month), day=int(day),
                                hour=int(hour), minute=int(minute), second=int(sec), microsecond=int(microS))
    elif isinstance(inputDT, (datetime.datetime, datetime.time)):
        outputTimeObj = inputDT
    elif isinstance(inputDT, UTCDateTime):
        outputTimeObj = inputDT.datetime

    # Add timezone info
    availableTimezones = list(map(str.lower, zoneinfo.available_timezones()))
    if outputTimeObj.tzinfo is not None and outputTimeObj.tzinfo.utcoffset(outputTimeObj) is not None:
        # This is already timezone aware
        pass
    elif type(tzone) is int:
        outputTimeObj = outputTimeObj-datetime.timedelta(hours=tzone)
    elif type(tzone) is str:
        if tzone.lower() in availableTimezones:
            outputTimeObj = outputTimeObj.replace(tzinfo=zoneinfo.ZoneInfo(tzone))
        else:
            raise ValueError("Timezone {} is not in official list. \nAvailable timezones:\n{}".format(tzone, availableTimezones))
    elif isinstance(tzone, zoneinfo.ZoneInfo):
        outputTimeObj = outputTimeObj.replace(tzinfo=tzone)
    else:
        raise ValueError("Timezone must be either str, int, or zoneinfo.ZoneInfo object")

    # Convert to UTC
    outputTimeObj = outputTimeObj.astimezone(datetime.timezone.utc)

    return outputTimeObj


#Get character for printing
def _get_char(in_char):
    """Outputs character with proper encoding/decoding"""
    if in_char in greek_chars.keys():
        out_char = greek_chars[in_char].encode(encoding='utf-8')
    else:
        out_char = in_char.encode(encoding='utf-8')
    return out_char.decode('utf-8')


# Get default dictionary with keys=parameter names and values=default values
def _get_default_args(func):
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
        }
    

# Get fuller traceback information on errors
def _get_error_from_exception(exception=None, print_error_message=True, return_error_message=False):
    if exception is not None:
        traceback.print_exception(sys.exc_info()[1])
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        errLineNo = str(traceback.extract_tb(sys.exc_info()[2])[-1].lineno)
        error_category = type(exception).__name__.title().replace('error', 'Error')
        error_message = f"{exception} ({errLineNo})"
        
        if print_error_message:
            print(f"{error_category} ({errLineNo}): {error_message}")
            print(lineno, filename, f)
        
        if return_error_message:
            return f"{error_category} ({errLineNo}): {error_message}\n\n{lineno} {filename} {f}"


#Check that input strema has Z, E, N channels
def _has_required_channels(stream):
    channel_set = set()
    
    # Extract the channel codes from the traces in the stream
    for trace in stream:
        channel_set.add(trace.stats.channel)
    
    # Check if Z, E, and N channels are present
    return {'Z', 'E', 'N'}.issubset(channel_set)

#Make input data (dict) into sprit_hvsr class
def _make_it_classy(input_data, verbose=False):
    if isinstance(input_data, (sprit_hvsr.HVSRData, sprit_hvsr.HVSRBatch)):
        for k, v in input_data.items():
            if k=='input_params':
                for kin in input_data['input_params'].keys():
                    if kin not in input_data.keys():
                        input_data[kin] = input_data['input_params'][kin]
            if k=='params':
                for kin in input_data['params'].keys():
                    if kin not in input_data.keys():
                        input_data[kin] = input_data['params'][kin]                
        output_class = input_data
    else:
        output_class = sprit_hvsr.HVSRData(input_data)
    if verbose:
        print('Made it classy | {} --> {}'.format(type(input_data), type(output_class)))
    return output_class


#Read data directly from Raspberry Shake
def _read_from_RS(dest, src='SHAKENAME@HOSTNAME:/opt/data/archive/YEAR/AM/STATION/', opts='az', username='myshake', password='shakeme',hostname='rs.local', year='2023', sta='RAC84',sleep_time=0.1, verbose=True, save_progress=True, method='scp'):
    src = src.replace('SHAKENAME', username)
    src = src.replace('SHAKENAME', hostname)
    src = src.replace('YEAR', year)
    src = src.replace('STATION', sta)

    if method == 'src':
        """This does not work from within a virtual environment!!!!"""
        #import pexpect
        import sys
        #from pexpect import popen_spawn
        import time
        import wexpect

        scp_command = 'scp -r {} "{}"'.format(src, dest)

        print('Command:', scp_command)
        child = wexpect.spawn(scp_command, timeout=5)

        child.expect("password:")
        child.sendline(password)

        child.expect(wexpect.EOF)

        print("Files have been successfully transferred to {}!".format(dest))
    elif method=='rsync':
        if verbose:
            opts = opts + 'v'
        if save_progress:
            opts = opts + 'p'   

        #import subprocess
        #subprocess.run(["rsync", "-"+opts, src, dest])
        #subprocess.run(["rsync", "-"+opts, src, dest])

        import pty
        #Test, from https://stackoverflow.com/questions/13041732/ssh-password-through-python-subprocess
        command = [
            'rsync',
            "-"+opts,
            src,
            dest
            #'{0}@{1}'.format(shakename, hostname),
            #'-o', 'NumberOfPasswordPrompts=1',
            #'sleep {0}'.format(sleep_time),
        ]

        # PID = 0 for child, and the PID of the child for the parent    
        pid, child_fd = pty.fork()

        if not pid: # Child process
            # Replace child process with our SSH process
            os.execv(command[0], command)

        while True:
            output = os.read(child_fd, 1024).strip()
            lower = output.lower()
            # Write the password
            if lower.endswith('password:'):
                os.write(child_fd, password + '\n')
                break
            elif 'are you sure you want to continue connecting' in lower:
                # Adding key to known_hosts
                os.write(child_fd, 'yes\n')
            elif 'company privacy warning' in lower:
                pass # This is an understood message
            else:
                print("SSH Connection Failed",
                    "Encountered unrecognized message when spawning "
                    "the SSH tunnel: '{0}'".format(output))

    return dest


def _run_docstring():
    """This function updates the docstring the sprit.run() function, for documentation or help(sprit.run()) purposes

    Returns
    -------
    str
        Updated Docstring with more specifics about functions and their parameters
    """
    nl = '\n\t'
    dsIntro = sprit_hvsr.run.__doc__.split('Parameters')[0]
    dsParameters = ('Parameters'+sprit_hvsr.run.__doc__.split('Parameters')[1].split('Returns')[0])
    dsReturns = ('    Returns'+sprit_hvsr.run.__doc__.split('Returns')[1])
    
    functionList = [sprit_hvsr.input_params, sprit_hvsr.fetch_data, sprit_hvsr.calculate_azimuth,
                    sprit_hvsr.remove_noise, sprit_hvsr.generate_psds, sprit_hvsr.process_hvsr, 
                    sprit_hvsr.remove_outlier_curves, sprit_hvsr.check_peaks, 
                    sprit_hvsr.get_report, sprit_hvsr.export_hvsr]

    funcStrList = []
    funcParams = []
    funcDefaults = []
    prevOutputList = ['params', 'hvsr_data', 'hvsr_results']
    requiredList = []
    for func in functionList:
        parameters = inspect.signature(func).parameters
        defaults = [param.default for param in list(zip(*parameters.items()))[1]]
        parameters = list(zip(*parameters.items()))[0]

        for i, d in enumerate(defaults):
            if 'kwargs' in parameters[i]:
                defaults[i] = {}
            elif d is inspect._empty:
                if any(o in parameters[i] for o in prevOutputList):
                    defaults[i] = '<output of previous function>'
                else:
                    defaults[i] = '<no default>'

        funcDS = func.__doc__.split('\n')[0][:100]
        baseURL = r"https://sprit.readthedocs.io/en/latest/sprit.html#sprit."
        funcURL = baseURL+func.__name__
        firstLine = f"\n    {func.__name__} : function name (not an actual parameter) \n\t{funcDS}\n\tSee API documentation: [{func.__name__}()]({funcURL})"
        followingLines = ''
        for i, param in enumerate(parameters):
            followingLines += f"\n    {param}"#.ljust(25)
            if isinstance(defaults[i], str) and defaults[i]!='<positional, no default>':
                followingLines += f": any, default = '{defaults[i]}'\n\tSee API documentation at link above or at `help(sprit.{func.__name__})` for specifics."
            else:
                followingLines += f": any, default = {defaults[i]}\n\tSee API documentation at link above or at `help({func.__name__})` for specifics."

        #funcDefaults.append(['<positional, no default>' if d is inspect._empty else d for d in defaults])
        #funcParams.append(list(zip(*parameters.items()))[0])

        funcString = firstLine + followingLines
        funcStrList.append(funcString)

    run_docstring = dsIntro + dsParameters + f"{nl.join(funcStrList)}\n\n" + dsReturns
    return run_docstring


# Time functions, for timing how long a process takes
def _time_it(_t, proc_name='', verbose=True):
    """Computes elapsed time since the last call."""
    
    t1 = datetime.datetime.now().time()
    dt = t1 - _t
    t = _t
    if dt > 0.05:
        if verbose:
            print(f'[ELAPSED TIME] {dt:0.1f} s', flush=True)
        t = t1
    return t


#Get x mark (for negative test results)
def _x_mark(incolor=False, inTerminal=False):
    """The default Windows terminal is not able to display the check mark character correctly.
       This function returns another displayable character if platform is Windows"""
    
    if incolor:
        try:
            xmark = _get_char(u'\u274C')
        except Exception:
            xmark = _get_char(u'\u2718')
    else:
        xmark = _get_char(u'\u2718')
    return xmark
