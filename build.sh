#!/bin/bash

pip_file="requirements.txt"
venv=".venv"
exec_command="/bin/python3 dealsBot.py"

setup_env() {
    # Create virtual env
    if python3 -m venv $venv; then 
        echo "Created Python virtual env in folder $venv"
    else   
        echo "Failed to create virtual env"
    fi 

    #Source activate script for virutal env
    activate

    # Install project dependencies
    if pip install -r $pip_file; then
        echo "Installed project dependencies from $pip_file"
    else 
        echo "Failed to install project depenencies from $pip_file. Please check if exists."
    fi
}

freeze() {
    if pip freeze > $pip_file; then 
        echo "Env dependencies set in $pip_file"
    else 
        echo "Failed to freeze dependencies in $pip_file"
    fi
}

run() {
    $exec_command
}

activate() {
    #Source activate script for virutal env
    source "$venv/bin/activate"
}

print_env() {
    pip -V
}

help() {
cat << EOF 
usage: build.sh [--help | -H][--setup | -S ][--freeze | -F][--activate | -A][--venv | -V][--exec | -E]

--help | -H
    Displays command positional arguments

--setup | -S 
    Creates a new Python3 Virtual Environment, activates it and installs relevant dependencies from $pip_file

--freeze | -F
    Takes snapshot of environemnt depenencies into a file called $pip_file

--activate | -A 
    Activates the virtual environemnt, set to $venv

--venv | -V 
    Lists the current pip environment

--exec | -E
    Runs the project

EOF
}



while [[ "$1" =~ ^- && ! "$1" == "--" ]]; do case $1 in
  -H | --help )
    help
    ;;
  -S | --setup )
    setup_env
    ;;
  -F | --freeze )
    freeze
    ;;
  -A | --activate )
    activate
    ;;
  -V | --venv )
    print_env
    ;;
  -E | --exec )
    run
    ;;
esac; shift; done
if [[ "$1" == '--' ]]; then shift; fi