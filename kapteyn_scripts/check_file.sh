#!/usr/bin/bash
file_path=$1
if [[ -d "$file_path" ]]
    then echo "1"
    else echo "0" 
fi