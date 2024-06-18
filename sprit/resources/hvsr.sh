#!/bin/bash
# This will be used to do site-based analysis on raspberry shake instruments.
# This is very much a work in progress
SITE_NAME="HVSRSite"
DURATION=20
CHECK_INT=5
VERBOSE=""
SYS_IS_RS=false
STATION="REDA9"
HVSR_DIR="./hvsr"

# Get options
while getopts 'n:d:v:c:' opt; do
    case "$opt" in
        n) SITE_NAME="$OPTARG";;
        d) DURATION="$OPTARG";;
        c) CHECK_INT="$OPTARG";;
        v) VERBOSE="-v";;
        ?|h)
            echo "Usage: $(basename "$0") [-n site_name] [-d DURATION in minutes]"
            exit 1
            ;;
    esac
done

# Shift the parsed options
shift "$((OPTIND - 1))"

read mindur mindecdur <<< $(echo $DURATION | awk -F. '{print $1, $2}')

S_DURATION=$(($((mindur * 60))+$((mindecdur*6))))

# Now you use the variables in your script
echo "Acquiring data for $SITE_NAME"
echo "Acquisition will last for $DURATION minutes ($S_DURATION seconds)"

START_TIME=$(date +'%Y-%m-%d %T')
START_TIMESTAMP=$(date +%s)

END_TIME=$(date -d "$date $S_DURATION seconds" +'%Y-%m-%d %T')
END_HOUR=$(date -d "$date $S_DURATION seconds" +'%H')
END_MIN=$(date -d "$date $S_DURATION seconds" +'%M')
END_SEC=$(date -d "$date $S_DURATION seconds" +'%S')
END_TIMESTAMP=$(date -d "$date $S_DURATION seconds" +'%s')

UTC_DIFF=$(date +%:::z)

echo "  $(date)"
echo "  Start time is $(date -d "$START_TIME" +'%H:%M') (UTC $UTC_DIFF)"
echo "  End time is   $(date -d "$END_TIME" +'%H:%M') (UTC $UTC_DIFF)"
echo "  ----------------------------------------------------------------------"

CURRENT_TIMESTAMP=$(date +%s)

while [[ $CURRENT_TIMESTAMP < $END_TIMESTAMP ]]; do
    CURRENT_TIMESTAMP=$(date +%s)
    MIN_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)/60))
    SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP) - ($MIN_REMAINING*60)))
    TOT_SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)))
    printf "    %02d:%02d Remaining   |  CURRENT TIME: $(date +%T)  |  END TIME: $(date -d "$END_TIME" '+%T')\n" $MIN_REMAINING $SEC_REMAINING

    if [ $CHECK_INT -lt $TOT_SEC_REMAINING ]; then
        sleep $CHECK_INT
    else
        sleep $TOT_SEC_REMAINING
    fi
    CURRENT_TIMESTAMP=$(date +%s)
done

echo "  ----------------------------------------------------------------------"
echo ""
echo "ACQUISITION COMPLETED"

# Data Clean up
echo "Cleaning up data now"

#Use slinktool to move and combine data
if [ ! -d $HVSR_DIR ]; then
    mkdir "$HVSR_DIR"
fi

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

fpath="$HVSR_DIR/"$SITE_NAME"_$(date -d "$START_TIME" '+%H%M')-$(date -d "$END_TIME" '+%H%M').mseed"
echo "Exporting site data to  $fpath"
slinktool -S "AM_$STATION:EH?" -tw "$sTIME:$eTIME" -o $fpath $VERBOSE :18000

#RASPBERY SHAKE SYSTEM CHECK HERE
if $SYS_IS_RS; then
    echo "POWERING DOWN"
    sudo poweroff
else
    echo "Program Completed. If this was a Raspberry Shake, your system would shut down now."
fi
