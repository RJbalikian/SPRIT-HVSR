#!/bin/bash
set -e
#VERSIONING
SCRIPT_VERSION="v1.3"
SCRIPT_UPDATE="2025-06-02"

#DESCRIPTION
# This will be used to do site-based analysis on raspberry shake instruments.
# This is very much a work in progress
USAGE_TEXT="Usage: $(basename "$0") CAPITALIZED WORD after option indicates variable to which that argument gets passed.\n\n\t\
OPTION |   ARGUMENT   | DESCRIPTION       \n\t\
-------|--------------|-------------------\n\t\
 -n    | SITE_NAME    | Name of site; this will be used as the first part of the filename; defaults to 'HVSRSite'\n\t\
 -d    | DURATION     | Duration of HVSR acquisition, in minutes (default is 20 min; up to one decimal point supported)\n\t\
 -c    | CHECK_INT    | The interval at which to check/print status, in seconds (default is 30 sec)\n\t\
 -s    | STARTUP_TIME | The amount of time between when the hvsr command is run and when data is saved, in seconds (default is 15 sec)\n\t\
 -t    |              | Run this site as a test (does not save data or turn off Shake)\n\t\
 -v    |              | Print information to terminal in verbose manner\n\t\
 -h    |              | Print this help message (-h should only be used by itself)\n\t\
 -e    | EXPORT_DISK* | EXPORT_DISK argument is optional; Export data in /opt/hvsr/data folder to inserted USB disk (experimental)\n\n"

#CODE

# ESTABLISH DEFAULT PARAMETERS
# Default variable values
SITE_NAME="HVSRSite"
DURATION=20
CHECK_INT=30
VERBOSE=""

RUN_AS_TEST=false
TEST_TEXT=""
CURR_YEAR=$(date +'%Y')
STATION=$(ls "/opt/data/archive/$CURR_YEAR/AM")
HVSR_DIR="/opt/hvsr"
HVSRDATA_DIR="/opt/hvsr/data"
EXPORT_DISK="/dev/sda1"

# Time to wait for startup and powerdown at start/after end of acquisition.PDOWN_TIME Not currently used
STARTUP_TIME=15
# PDOWN_TIME=30

# Parse out help command only
if [ "$1" == "-h" ] ; then
    printf "$USAGE_TEXT"
    exit 0
fi

# READ IN OPTIONS
# Get options
while getopts 'n:t:d:c:s:h:ve' opt; do
    case "$opt" in
        n) SITE_NAME="$OPTARG"
            echo $SITE_NAME
            ;;
        t) RUN_AS_TEST=true
            TEST_TEXT="RUNNING SITE AS TEST (will not power off instrument)";;
        d) DURATION="$OPTARG";;
        c) CHECK_INT="$OPTARG";;
        s) STARTUP_TIME="$OPTARG";;
        v) VERBOSE="-v";;
        e)
            # Not sure how this works, but it does
            # Check next positional parameter
            eval nextopt=\${$OPTIND}
            # existing or starting with dash?
            if [[ -n $nextopt && $nextopt != -* ]] ; then
                OPTIND=$((OPTIND + 1))
                level=$nextopt
            else
                level=1
            fi

            # Get specified export disk, or use last (alphabetic) detected one
            if [[ -n "$nextopt" ]]; then
                EXPORT_DISK="$nextopt"

                if ! [[ $EXPORT_DISK =~ ^[0-9]{1,3}$ ]]; then
                    echo "$EXPORT_DISK specified as export disk"
		        else
                    EXPORT_DATE=$(printf "%03d" "$EXPORT_DISK")
                    USBDISKS=$(readlink -f /dev/disk/by-id/usb*)
                    while read dev;do
                        LASTDISK=$dev;
                    done <<< $USBDISKS
                    echo $LASTDISK

                    EXPORT_DISK=$LASTDISK
                    echo "Exporting files on USB disk detected at $EXPORT_DISK from day $EXPORT_DATE"
                fi

            else
                # Handle the case when the argument is missing
                USBDISKS=$(readlink -f /dev/disk/by-id/usb*)

                # Detect USB drives
                while read dev;do
                    LASTDISK=$dev;
                done <<< $USBDISKS
		        echo $LASTDISK

		        EXPORT_DISK=$LASTDISK

                if [[ -z "$EXPORT_DISK" ]]; then
                    echo "No USB disks detected. Data not exported"
                    # If not specified and not detected, exit and do not export
                    exit 1
                else
                    echo "No export disk specified, using USB disk detected at $EXPORT_DISK"
                fi
            fi

            if [[ "$USBDISKS" == *"$EXPORT_DISK"* ]]; then
                echo "Your specified disk is a USB disk"
            else
                # Check if Export disk is an output of the USBDISKS disk identifier
                echo "Your specified disk is not a USB disk. Cannot export data"
                exit 1
            fi

            # Mount and change disk/directory name
	        # We will mount to "usbdrive" folder temporarily
            MOUNTED_DIR="/mnt/usbdrive/"
            # Make that directory if it doesn't exist
            if [ ! -d $MOUNTED_DIR ]; then
                sudo mkdir $MOUNTED_DIR
            fi
            # And mount the disk to that location
	        sudo mount $EXPORT_DISK $MOUNTED_DIR

            # Create folder to hold all exported data
            datestring=$(date +'%j_%Y-%m-%d_%H-%M-%S')
            EXPORT_DIR="${MOUNTED_DIR%/}/EXPORT_&STATION_$datestring/"

            # Create export directory on usb drive
            if [ ! -d $EXPORT_DIR ]; then
                sudo mkdir "$EXPORT_DIR"
            fi

            # Copy data to USB drive
            if [ -z $EXPORT_DATE ]; then
                echo "Copying data from $HVSRDATA_DIR to $EXPORT_DIR"
                sudo cp -r "$HVSRDATA_DIR/"* "$EXPORT_DIR"
	        else
                echo "Copying data from day $EXPORT_DATE from $HVSRDATA_DIR to $EXPORT_DIR" 
                find "$HVSRDATA_DIR" -type f -name "*_$EXPORT_DATE_*" -exec cp {} "$EXPORT_DIR" \;
            fi

            # Clean up everything and confirm copy
            echo "Data successfully copied to $datestring folder on USB device $EXPORT_DISK"
	        sudo umount $EXPORT_DISK
	        echo "$EXPORT_DISK successfully unmounted, you may now remove drive"
            exit 0
            ;;
	  \?) printf "$USAGE_TEXT" exit 1 ;;
    esac
done

# Shift the parsed options
shift "$((OPTIND - 1))"

# If the minutes entered for duration were decimal, extract each part
read mindur mindecdur <<< $(echo $DURATION | awk -F. '{print $1, $2}')
mindecdur=$(printf %.1s "$mindecdur")

# Now get the duration in seconds
S_DURATION=$(($((mindur * 60))+$((mindecdur*6))))
START_TIME=$(date -d "@$(( $(date +%s) + $STARTUP_TIME ))" +"%H:%M:%S")
START_TIMESTAMP=$(date -d "@$(( $(date +%s) + $STARTUP_TIME ))" +"%s")
END_TIMESTAMP=$(date -d "@$(( $(date +%s) + $STARTUP_TIME + $S_DURATION ))" +"%s")
END_TIME=$(date -d @"$END_TIMESTAMP" +"%H:%M:%S")

# START HVSR PROCESS
# Print out information
echo "HVSR SCRIPT VERSION $SCRIPT_VERSION"
echo "LAST UPDATED $SCRIPT_UPDATE"
echo "$TEST_TEXT"
echo ""
echo "---------------------------------------------------------------------"
echo "                            SITE INFORMATION"
echo "---------------------------------------------------------------------"
echo "STATION             |  $STATION"
echo "SITE NAME           |  $SITE_NAME"
echo "DURATION            |  $DURATION minutes ($S_DURATION seconds)"
echo "ACQUISITION DATE    |  $(date) ($(date +"%Y-%m-%d"))"
echo "  DAY OF YEAR       |  $(date +%j)"
echo "START TIME          |  $START_TIME"
echo "END TIME            |  $END_TIME"
echo "---------------------------------------------------------------------"
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
echo "ACQUISITION COMPLETED!"
echo ""

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

fpath="$HVSRDATA_DIR/"$SITE_NAME"_"$STATION"_$(date -d "$START_TIME" '+%j_%Y-%m-%d_%H%M')-$(date -d "$END_TIME" '+%H%M').mseed"
echo "Exporting site data to  $fpath"

# slinktool will query data on shake, between start and end time, and save it as an mseed file in HVSR_DIR
slinktool -S "AM_$STATION:EH?" -tw "$sTIME:$eTIME" -o "$fpath" $VERBOSE :18000

#RASPBERRY SHAKE SYSTEM CHECK HERE
# If this is being run on a raspberry shake, poweroff instrument
if ! $RUN_AS_TEST; then
    # Shutdown instrument
    echo "Powering down in 5 seconds"
    sleep 5
    sudo poweroff
else
    echo "Program Completed. If this was a not a test, your Raspbery Pi system would shut down now."
fi

echo "Program will end in 10 seconds"
sleep 10
