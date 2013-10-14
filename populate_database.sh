#!/bin/bash

if [ -z $1 ]
then
    echo "$(tput bold)$(tput setaf 1)Error: no arguments given! You must supply the name of the script to use.$(tput sgr0)"
else
    PREFIX="populate-"
    SCRIPT_PATH="./mysite/scripts/populate-with-data/$PREFIX$1.py"
    echo -e "$(tput bold)$(tput setaf 3)Executing script $SCRIPT_PATH$(tput sgr0)"
    python $SCRIPT_PATH "db=./mysite/site.db" "$@"
fi
