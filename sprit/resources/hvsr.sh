#!/bin/bash
# This will be used to do site-based analysis on raspberry shake instruments.
# This is very much a work in progress
site_name="HVSR Site"
duration=20

# Get options
while getopts 'n:d:' opt; do
    case "$opt" in
        n) site_name="$OPTARG";;
        d) duration="$OPTARG";;
        ?|h)
            echo "Usage: $(basename "$0") [-n site_name] [-d duration in minutes]"
            exit 1
            ;;
    esac
done

# Shift the parsed options
shift "$((OPTIND - 1))"

# Now you use the variables in your script
echo "Acquiring data for $site_name"
echo "Acquisition will last for $duration minutes"

start_time=$(date +%H:%M)
end_time=$(date -d "$date $duration minutes" +'%H:%M')
tzone_diff=$(date +%:::z)

echo "  Start time is $start_time (UTC $tzone_diff)"
echo "  End time is   $end_time (UTC $tzone_diff)"
