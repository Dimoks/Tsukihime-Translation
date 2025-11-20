#!/bin/bash
echo "Start $(basename "$0") $(date "+%d.%m.%Y %H:%M:%S,%3N")" >> log.txt
start_time=$(date +%s.%N)

python3 patch_allpac.py tsuki_re_ja allpac

end_time=$(date +%s.%N)
echo "End $(basename "$0") $(date "+%d.%m.%Y %H:%M:%S,%3N")" >> log.txt
execution_time=$(echo "$end_time - $start_time" | bc)

total_seconds=$(echo "$execution_time" | awk '{print int($1)}')
ms=$(echo "$execution_time * 1000" | bc -l | awk '{print int($1 % 1000)}')

hours=$((total_seconds / 3600))
minutes=$(( (total_seconds % 3600) / 60 ))
seconds=$((total_seconds % 60))
printf "Work Time: %d:%02d:%02d,%03d\n" $hours $minutes $seconds $ms | tee -a log.txt
echo ------------------------>>log.txt