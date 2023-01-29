"""
 IRIS HVSR

 DESCRIPTION
 computeHVSR.py configuration parameters

 HISTORY
  2020-02-24 IRIS DMC Product Team (Manoch): added reportDirectory V.2020.055
  2019-07-31 IRIS DMC Product Team (Manoch): style update V.2019.212
  2018-07-10 IRIS DMC Product Team (Manoch): pre-release V.2018.191
  2018-06-18 IRIS DMC Product Team (Manoch): added removeOutliers parameter to allow HVSR computation without 
                      removing outliers and added method parameter that indicates the method to use for 
                      combining h1 and h2
  2017-11-28 IRIS DMC Product Team (Manoch): V.2017332
  2015-05-19 IRIS DMC Product Team (Manoch): created R.2017139

 NOTES

"""
import os
import sys
import json
import datetime

import hvsr.pyUpdates.ioput as ioput
import hvsr.pyUpdates.fileLib as fileLib


args = { 'net':'AM',
        'sta':'RAC84',
        'loc':'00',
        'cha': ['EHZ', 'EHN', 'EHE']
        }

def defineInputParameters(network='AM', 
                        station='RAC84', 
                        loc='00', 
                        channels=['EHZ', 'EHN', 'EHE'],
                        date=datetime.datetime.now().date,
                        starttime = '00:00:00.00',
                        endtime = '23:59:99.99',
                        tzone = 'America/Chicago', #or 'UTC'
                        lon = -88.2290526,
                        lat =  40.1012122,
                        elevation = 755,
                        depth = 0
                        ):
    #day_of_year = 1#Get day of year
    #Reformat time
    starthour = starttime.split(':')[0]
    startminute = starttime.split(':')[1]
    startsecond = starttime.split(':')[2]

    starttime = datetime.datetime(date.year, date.month, date.day,
                                starthour, startminute, startsecond,tzinfo=tzone)

    endhour = endtime.split(':')[0]
    endminute = endtime.split(':')[1]
    endsecond = endtime.split(':')[2]

    endtime = datetime.datetime(date.year, date.month, date.day,
                                endhour, endminute, endsecond)

    if tzone.upper() == 'local':
        tzone = 'America/Chicago'

    if tzone.upper() == 'UTC':
        pass
    else:
        starttime= datetime.timezone.fromutc(starttime)
        endtime=endtime #reformat time to UTC
        year = starttime.year()

    inputParamDict = {'net':network,'sta':station, 'loc':loc, 'cha':channels,
                    'date':date,'starttime':starttime,'endtime':endtime, 
                    'longitude':lon,'latitude':lat,'elevation':elevation,'depth':depth,
                    }

    return inputParamDict

##HERE
def setShakeMetadata(filepath, startDate='2022-10-22', endDate=datetime.datetime.today(), lon, lat, createDate, elevation, depth):
    filepath = ioput.checkifpath(filepath)
    
    with open(filepath , 'r') as f:
        metadata = json.load(filepath)
    print(metadata.keys())
    return

parentDirectory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# import the libraries
libraryPath = os.path.join(parentDirectory, 'lib')
sys.path.append(libraryPath)

verbose = 1

# URLs
mustangPsdUrl = 'http://service.iris.edu/mustang/noise-psd/1/query?'
mustangPdfUrl = 'http://service.iris.edu/mustang/noise-pdf/1/query?'

# Directories
dataDirectory = fileLib.mkdir(parentDirectory, 'data')
imageDirectory = fileLib.mkdir(parentDirectory, os.path.join('image', 'hvsr'))
workDir = fileLib.mkdir(parentDirectory, 'scratch')
baselineDirectory = fileLib.mkdir(dataDirectory, 'baseline')
reportDirectory = fileLib.mkdir(dataDirectory, 'report')
hvsrDirectory = fileLib.mkdir(dataDirectory, 'hvsr')

# Default station channel list.
#chan = 'BHZ,BHN,BHE' #From original code
chan = 'EHZ, EHN, EHE' #For rasp shake
channel_order = {'Z': 0, '1': 1, 'N': 1, '2': 2, 'E': 2}

# Should break the long requested interval to 'n' segments for smaller data request chunks.
# Increase 'n' when requesting long time intervals to avoid request failures.
n = 1

# Define x-axis  type (period or frequency).
xtype = 'frequency'
hvsrband = [0.2, 15]

# should we remove outliers? (0|1)
removeoutliers = 1

# minimum peak amplitude to be considered. By increasing the waterlevel, you will reduce the sensitivity of
# peak picking.
waterlevel = 1.8

# minimum rank to be accepted
minrank = 2

# H is computed based on the selected method for combining h1 and h2
#     see: https://academic.oup.com/gji/article/194/2/936/597415 FOR METHODS 2-6
#     method:
#        (1) Diffuse Field Assumption
#        (2) arithmetic mean H = (HN + HE)/2 (the horizontal components are combined by using a simple mean)
#        (3) geometric mean H = Sqrt(HN . HE) (mean horizontal spectra is derived by taking square-root of the
#            product of the two horizontal components)
#        (4) vector summation H = Sqrt(N^2 + E^2)
#        (5) quadratic mean H = Sqrt((N^2 + E^2)/2.0)
#        (6) maximum horizontal value H = Max(HN, HE)
methodList = ['', 'Diffuse Field Assumption', 'arithmetic mean', 'geometric mean', 'vector summation',
              'quadratic mean', 'maximum horizontal value']

method = 4

# plot
plot = 1
plotnnm = 1
showplot = 1
plotpsd = 0
plotpdf = 1
plotbad = 0
yLabel = 'Power (dB)'
xLabel = {'frequency': 'Frequency (Hz)', 'period': 'Period (s)'}
xLim = {'frequency': [0.001, 20], 'period': [0.1, 120]}
yLim = [-200,-50]
#yLim = [-150,-70]
#yLim = [-200,-100]

hvsrylim = [0,10]
hvsrXlim = hvsrband
hvsrYlabel = 'HVSR'


pMin = -0.5
pMax = 30

colorLow = 'blue'
colorMid = 'yellow'
colorHigh = 'red'
imageDpi = 150
imageSize = [8, 16]
alpha = 0.7
lw = 3
