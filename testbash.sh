LINES=$(tput lines)

while true; do
    sprit sample --suppress_report_outputs
    sleep 2
    
    # Move cursor back up to overwrite plot
    # Move back number of lines
    printf "\033[${LINES}A"
    # Erase until end of terminal
    printf "\033[J"
done