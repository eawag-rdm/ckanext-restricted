# the script will get three arguments:
# 1. the name of the virtualenv
# 2. python version
# 3. ckan version

# function that reads the script arguments
function read_arguments {
    if [ $# -ne 3 ]; then
        echo "Usage: $0 <uv/pip> <python_version> <ckan_version>"
        exit 1
    fi
    
    # version number are like x.x.x
    INSTALL_WITH_UV=$1
    PYTHON_VERSION=$2
    CKAN_VERSION=$3

    # create the name of the venv replace '.' of the versions with '-'
    VIRTUALENV_NAME=".venv_py${PYTHON_VERSION//./-}_ckan${CKAN_VERSION//./-}"

}

# check if the virtualenv exists and delete it if it does
function check_virtualenv {
    if [ -d $VIRTUALENV_NAME ]; then
        echo "Deleting virtualenv $VIRTUALENV_NAME"
        rm -rf $VIRTUALENV_NAME
    fi
}

# check if 'uv' is installed other wise abort with warning that uv needs to be installed
function check_uv {
    if ! which uv > /dev/null; then
        echo "uv is not installed. Please install it first."
        exit 1
    fi
}

# install python version with uv, if it does not exist
function install_python {
    if ! uv python find $PYTHON_VERSION > /dev/null; then
        # if this fails, the script will exit
        if ! uv python install $PYTHON_VERSION; then
            echo "Failed to install python $PYTHON_VERSION"
            exit 1
        fi
    fi
}


function install_ckan_with_uv {
    uv venv --python=$PYTHON_VERSION $VIRTUALENV_NAME

    source $VIRTUALENV_NAME/bin/activate    

    uv pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/requirement-setuptools.txt
    uv pip install git+https://github.com/ckan/ckan.git@$CKAN_VERSION#egg=ckan[requirements]

    uv pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/dev-requirements.txt
    uv pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/requirements.txt
    
}

function install_ckan_with_pip {
    $(uv python find $PYTHON_VERSION) -m venv $VIRTUALENV_NAME

    source $VIRTUALENV_NAME/bin/activate

    pip install --upgrade pip==22.0.4
    pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/requirement-setuptools.txt
    pip install -e "git+https://github.com/ckan/ckan.git@$CKAN_VERSION#egg=ckan[requirements]"

    pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/dev-requirements.txt
    pip install -r https://raw.githubusercontent.com/ckan/ckan/$CKAN_VERSION/requirements.txt
    
}

function install {
    if [ $INSTALL_WITH_UV == "uv" ]; then
        install_ckan_with_uv
    else
        install_ckan_with_pip 
    fi
}



# call all functions
read_arguments $@
check_virtualenv
check_uv
install_python
install

# working installs
# bash install_ckan.bash uv 3.9.20 2.10
# bash install_ckan.bash uv 3.10.11 2.10
# bash install_ckan.bash uv 3.11.10 2.10


