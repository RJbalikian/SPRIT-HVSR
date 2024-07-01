#!/bin/bash

# This will be used to do site-based analysis on raspberry shake instruments.
# This is very much a work in progress

# HANDLE SIGNAL DISCONNECT
# First, set up script to continue running even if there is a signal disconnect (SSH is disconnected)
# Function to handle disconnection
handle_disconnection() {
    echo "    Disconnected from SSH at $(date +'%T'). Continuing script execution..."
    trap ' ' HUP  # Ignore SIGHUP (hangup signal)
}

# Set up trap to handle SIGHUP (hangup signal)
trap handle_disconnection HUP

# NOW, ESTABLISH DEFAULT PARAMETERS
# Default variable values
SITE_NAME="HVSRSite"
DURATION=20
CHECK_INT=30
VERBOSE=""

SYS_IS_RS=false
CURR_YEAR=$(date +'%Y')
STATION=$(ls "/opt/data/archive/$CURR_YEAR/AM")
HVSR_DIR="/hvsr"
HVSRDATA_DIR="/hvsr/data"

# Time to wait for startup and powerdown at start/after end of acquisition.PDOWN_TIME Not currently used
STARTUP_TIME=15
# PDOWN_TIME=30

# READ IN OPTIONS
# Get options
while getopts 'n:d:v:c:' opt; do
    case "$opt" in
        n) SITE_NAME="$OPTARG";;
        d) DURATION="$OPTARG";;
        c) CHECK_INT="$OPTARG";;
        v) VERBOSE="-v";;
        ?|h)
            echo "Usage: $(basename "$0") [-n site_name] [-d DURATION of HVSR acquisition in minutes] [-c interval at which to check/print status] [-v verbose]"
            exit 1
            ;;
    esac
done

# Shift the parsed options
shift "$((OPTIND - 1))"

# If the minutes entered for duration were decimal, extract each part
read mindur mindecdur <<< $(echo $DURATION | awk -F. '{print $1, $2}')
mindecdur=$(printf %.1s "$mindecdur")

# Now get the duration in seconds
S_DURATION=$(($((mindur * 60))+$((mindecdur*6))))

# START HVSR PROCESS
# Print out progress
echo "Acquiring data for $SITE_NAME"
echo "Acquisition will last for $DURATION minutes ($S_DURATION seconds)"
echo "Acquisition Date: $(date) (Day of Year: $(date +%j))"
echo ""

while [[ $STARTUP_TIME > 0 ]]; do
    echo -ne "Beginning acquisition in $STARTUP_TIME seconds \033[0K\r"
    sleep 1
    STARTUP_TIME=$(($STARTUP_TIME - 1))
done

# Set the start time as current time
START_TIME=$(date +'%Y-%m-%d %T')
START_TIMESTAMP=$(date +%s)

# End time add duration to start time
END_TIME=$(date -d "$date $S_DURATION seconds" +'%Y-%m-%d %T')
END_HOUR=$(date -d "$date $S_DURATION seconds" +'%H')
END_MIN=$(date -d "$date $S_DURATION seconds" +'%M')
END_SEC=$(date -d "$date $S_DURATION seconds" +'%S')
END_TIMESTAMP=$(date -d "$date $S_DURATION seconds" +'%s')

UTC_DIFF=$(date +%:::z)

# Print out the times of everything
echo -ne "  Acquisition start time is $(date -d "$START_TIME" +'%H:%M') (UTC $UTC_DIFF)"
echo "  End time is   $(date -d "$END_TIME" +'%H:%M') (UTC $UTC_DIFF)"
echo "  ----------------------------------------------------------------------"

# Initialize current timestamp, which will be updated every check_int interval
CURRENT_TIMESTAMP=$(date +%s)

# Loop through every CHECK_INT seconds, print progress and keep it going until we reach desired time
while [[ $CURRENT_TIMESTAMP < $END_TIMESTAMP ]]; do
    # Get the timestamp for the current time
    CURRENT_TIMESTAMP=$(date +%s)

    # Calculate time remaining
    MIN_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)/60))
    SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP) - ($MIN_REMAINING*60)))
    TOT_SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)))
    printf "    %02d:%02d Remaining   |  CURRENT TIME: $(date +%T)  |  END TIME: $(date -d "$END_TIME" '+%T')\n" $MIN_REMAINING $SEC_REMAINING

    # Only for the last interval, where the check int is less than the total time remaining
    if [ $CHECK_INT -lt $TOT_SEC_REMAINING ]; then
        sleep $CHECK_INT
    else
        # Only sleep the amount of time left
        sleep $TOT_SEC_REMAINING
    fi
    # Get the timestamp for the current time again (to check against END_TIMESTAMP)
    CURRENT_TIMESTAMP=$(date +%s)
done

# Final printouts
echo "  ----------------------------------------------------------------------"
echo ""
echo "ACQUISITION COMPLETED"

# DATA CLEAN UP
echo "Cleaning up data now"

# Use slinktool to trim, combine, and export data
# First, create the directory to hold the data if it does not already exist
if [ ! -d $HVSR_DIR ]; then
    mkdir "$HVSR_DIR"
fi

if [ ! -d $HVSRDATA_DIR ]; then
    mkdir "$HVSRDATA_DIR"
fi

# Format the times to create a time window (-tw option)
sYEAR=$(date -d "$START_TIME" '+%Y')
sMON=$(date -d "$START_TIME" '+%m')
sDAY=$(date -d "$START_TIME" '+%d')
sHOUR=$(date -d "$START_TIME" '+%H')
sMIN=$(date -d "$START_TIME" '+%M')
sSEC=$(date -d "$START_TIME" '+%S')
sTIME="$sYEAR,$sMON,$sDAY,$sHOUR,$sMIN,$sSEC"

eYEAR=$(date -d "$END_TIME" '+%Y')
eMON=$(date -d "$END_TIME" '+%m')
eDAY=$(date -d "$END_TIME" '+%d')
eHOUR=$(date -d "$END_TIME" '+%H')
eMIN=$(date -d "$END_TIME" '+%M')
eSEC=$(date -d "$END_TIME" '+%S')
eTIME="$eYEAR,$eMON,$eDAY,$eHOUR,$eMIN,$eSEC"

fpath="$HVSRDATA_DIR/"$SITE_NAME"_$(date -d "$START_TIME" '+%Y-%m-%d_%j_%H%M')-$(date -d "$END_TIME" '+%H%M').mseed"
echo "Exporting site data to  $fpath"

# slinktool will query data on shake, between start and end time, and save it as an mseed file in HVSR_DIR
slinktool -S "AM_$STATION:EH?" -tw "$sTIME:$eTIME" -o $fpath $VERBOSE :18000

#RASPBERY SHAKE SYSTEM CHECK HERE

# If this is being run on a raspberry shake, poweroff instrument
if $SYS_IS_RS; then
    # Flash led in heartbeat mode
    modprobe ledtrig_heartbeat
    echo heartbeat >/sys/class/leds/led0/trigger

    # Do a powering down countdown
    #printf "Powering down in $PDOWN_TIME seconds"
    #while [[ $PDOWN_TIME > $0 ]]; do
    #    sleep 1
    #    PDOWN_TIME=$(($PDOWN_TIME - 1))
    #    echo -ne "Powering down in $PDOWN_TIME seconds \033[0K\r"
    #done
    echo "Powering down"
    sudo poweroff
else
    echo "Program Completed. If this was a Raspberry Shake, your system would shut down now."
fi
