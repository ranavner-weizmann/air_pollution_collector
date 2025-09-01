#!/bin/bash

# Define file paths and constants
FILE_PATH="/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/is_on.txt"
LOG_FILE="/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/boot_log.txt"
CUR_LOG_PATH="/home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors/main_log_path.txt"
COUNTER_PATH="Development/drone_dori/sensors/restart_counter.txt"
CONST_TIME_DIF=10

while true; do
    STATUS=$(cat "$FILE_PATH")
    echo "$STATUS"
    COUNTER=$(cat"$COUNTER_PATH")

    if pgrep runall; then
        ti_sys=$(date +%s)
        first_line=$(head -n 1 "$CUR_LOG_PATH" | tr -d '\n')
        dir=$(dirname "$first_line")
        latest_file=$(find "$dir" -type f -print0 | xargs -0 stat --format "%Y %n" | sort -nr | head -n1 | cut -d' ' -f2-)
        ti=$(stat -c %Y "$latest_file")
        diff=$((ti_sys - ti))
        echo "$diff"
        if ((diff < 0 )); then
            diff=$((-diff))
        fi
        if (( diff > CONST_TIME_DIF )); then
        # Change the content of is_on.txt to "booting"
                echo -n "booting" > "$FILE_PATH"

                # Log a message and timestamp
                echo "Boot initiated at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

                # Wait until the content of is_on.txt changes from "booting"
                while [ "$(cat "$FILE_PATH")" != "booting" ]; do
                    sleep 1
                done
                # Once the content is "booting," initiate a system reboot
                #sudo reboot
                echo "reboot"
                sleep 300
                break
        fi



    # Check if runall.py is already running
    elif [ "$STATUS" = "booting" ] && ! pgrep runall; then
        # Set the environment variables
        export SHELL=/bin/bash
        export TERM_PROGRAM_VERSION=1.81.1
        export COLORTERM=truecolor
        export LANG=en_US.UTF-8
        export LANGUAGE=en_US.UTF-8
        export NO_AT_BRIDGE=1
        export LC_ALL=en_US.UTF-8
        export PATH=/home/pi/evia/venv/bin:/home/pi/EPICS/epics-base/bin/linux-arm:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/games:/usr/games

        # Change directory and activate the virtual environment
        cd /home/pi/evia/WIS_air_pollution_surveyor/Development/drone_dori/sensors
        source /home/pi/evia/venv/bin/activate

        # Log a message and timestamp
        echo "Starting runall.py at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

        # Start runall.py
        ./runall.py
    fi 


            # Check if the status is "On"
    elif [ "$STATUS" = "On" ] && ! pgrep runall; then
        # Change the content of is_on.txt to "booting"
        echo -n "booting" > "$FILE_PATH"

        # Log a message and timestamp
        echo "Boot initiated at $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

        # Wait until the content of is_on.txt changes from "booting"
        while [ "$(cat "$FILE_PATH")" != "booting" ]; do
            sleep 1
        done

        # Once the content is "booting," initiate a system reboot
        #sudo reboot
        echo "reboot"
        sleep 300
        break
    fi

    sleep 3
done

echo "exited while true loop probably because of boot didnt happen yet" >> "$LOG_FILE"
