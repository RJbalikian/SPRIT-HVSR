#!/bin/bash
# This will be used to do site-based analysis on raspberry shake instruments.
# This is very much a work in progress
SITE_NAME="HVSR Site"
DURATION=20
CHECK_INT=5

SYS_IS_RS=false

# Get options
while getopts 'n:d:' opt; do
    case "$opt" in
        n) SITE_NAME="$OPTARG";;
        d) DURATION="$OPTARG";;
        ?|h)
            echo "Usage: $(basename "$0") [-n site_name] [-d DURATION in minutes]"
            exit 1
            ;;
    esac
done

# Shift the parsed options
shift "$((OPTIND - 1))"

read mindur mindecdur <<< $(echo $DURATION | awk -F. '{print $1, $2}')
echo "$mindur $mindecdur"
S_DURATION=$(($((mindur * 60))+$((mindecdur*6))))
echo $S_DURATION

# Now you use the variables in your script
echo "Acquiring data for $SITE_NAME"
echo "Acquisition will last for $DURATION minutes ($S_DURATION seconds)"

START_TIME=$(date +%H:%M:%S)
START_TIMESTAMP=$(date +%s)

END_TIME=$(date -d "$date $S_DURATION seconds" +'%H:%M:%S')
END_HOUR=$(date -d "$date $S_DURATION seconds" +'%H')
END_MIN=$(date -d "$date $S_DURATION seconds" +'%M')
END_SEC=$(date -d "$date $S_DURATION seconds" +'%S')
END_TIMESTAMP=$(date -d "$date $S_DURATION seconds" +'%s')

UTC_DIFF=$(date +%:::z)

echo "  $(date)"
echo "  Start time is $START_TIME (UTC $UTC_DIFF)"
echo "  End time is   $END_TIME (UTC $UTC_DIFF)"
echo "  ----------------------------------------------------------------------"

CURRENT_TIMESTAMP=$(date +%s)

while [[ $CURRENT_TIMESTAMP < $END_TIMESTAMP ]]; do
    CURRENT_TIMESTAMP=$(date +%s)
    MIN_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)/60))
    SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP) - ($MIN_REMAINING*60)))
    TOT_SEC_REMAINING=$(( ($END_TIMESTAMP - $CURRENT_TIMESTAMP)))
    printf "    %02d:%02d Remaining   |  CURRENT TIME: $(date +%T)  |  END TIME: $END_TIME\n" $MIN_REMAINING $SEC_REMAINING

    if [[ $CHECK_INT < $TOT_SEC_REMAINING ]]; then
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
echo "<Perform clean up tasks here>"
  #Use slinktool to copy and move data?

#RASPBERY SHAKE SYSTEM CHECK HERE

if $SYS_IS_RS; then
    echo "POWERING DOWN"
else
    echo "Program Completed. If this was a Raspberry Shake, your system would shut down now."
fi
