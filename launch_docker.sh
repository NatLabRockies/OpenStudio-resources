#!/bin/bash

# This script automates building a docker image, running a container, and running the regression tests
# It is a command line utility that asks you to make a few choices (with appropriate defaults in general)
# which abstracts the complexity of docker and makes it easy on the user to run tests for an older version
# For running multiple versions, see ./launch_all.sh

# AUTHOR: Julien Marrec, julien@effibem.com, 2018

# Import colors
source colors.sh

# Switch this to true to debug.
verbose=false

unameOut="$(uname -s)"
case "${unameOut}" in
  Linux*)     machine=Linux;;
  Darwin*)    machine=Darwin;;
  CYGWIN*|MINGW*|MSYS*)    machine=Windows;;
  *)          machine="UNKNOWN:${unameOut}"
esac

if [[ "$(arch)" == "arm64" ]]; then
  platform="--platform linux/amd64"
fi

########################################################################################

# Verbosity
if [ "$verbose" = true ]; then
  OUT=/dev/stdout
else
  # Pipe output of docker commands to /dev/null to supress them
  OUT=/dev/null
fi

# For msys (mingw), do not do path conversions '/' -> windows path
if [[ "$(uname)" = MINGW* ]]; then
  if [ "$verbose" = true ]; then
    echo
    echo "Note: Windows workaround: setting MSYS_NO_PATHCONV to True when calling docker"
  fi
  docker()
  {
    export MSYS_NO_PATHCONV=1
    ("docker.exe" "$@")
    export MSYS_NO_PATHCONV=0
  }
fi

########################################################################################
#                               A R G U M E N T S
########################################################################################


os_version=$1

if [ -z "$os_version" ]
then
  echo 'You must supply a version of OpenStudio to use, eg: ./launch_docker.sh "2.2.1"'
  exit 1
fi

echo -e "Running docker script for version ${BRed}$os_version${Color_Off}"


test_file=$2
if [ -z "$test_file" ]
then
  test_file="model_tests.rb"
  echo "Defaulted to $test_file"
fi


# Hardcoded arg
# Use mongo?
use_mongo=false

########################################################################################
#                               V A R I A B L E S
########################################################################################


# Image/Container names
mongo_image_name=mongo
mongo_container_name=openstudio-mongo

base_os_image_name=nrel/openstudio:$os_version
os_image_name=custom/openstudio:$os_version
os_container_name=my_openstudio

# String representation with colors
mongo_image_str="${BPurple}image${Color_Off} ${UPurple}$mongo_image_name${Color_Off}"
mongo_container_str="${BCyan}container${Color_Off} ${UCyan}$mongo_container_name${Color_Off}"

os_image_str="${BRed}image${Color_Off} ${URed}$os_image_name${Color_Off}"
os_container_str="${BBlue}container${Color_Off} ${UBlue}$os_container_name${Color_Off}"

base_os_image_str="${BRed}image${Color_Off} ${URed}$base_os_image_name${Color_Off}"


########################################################################################
#                           C L E A N    U P
########################################################################################

# This is defined here because I also run this when I catch CTRL+C
# It is also run at the end of the normal execution

# Note: There should be no need to clean up the container as long as you attach to it,
# I use --rm when launching the container

function stop_running_container() {
  # Arg 1 is the container_name
  # Arg 2 is the container_str with colors
  # Arg 3 is the default answer: pass Y for yes, N for no. Default Y
  # eg: stop_running_container "$os_container_name" "$os_container_str" N

  # If the container is still running, ask whether we stop it first
  if [ "$(docker ps -q -f name=$1)" ]; then
    if [[ $3 = N ]]; then
      echo -e -n "Do you want to stop the running $2? [y/${URed}N${Color_Off}] "
      read -n 1 -r
      echo    # (optional) move to a new line
      # Default is No
      if [[ $REPLY =~ ^[Yy]$ ]]
      then
        docker stop $1> $OUT
        echo -e "* Stopped the $2"
      else
        echo -e "* You can attach to the running container by typing '${Green}docker attach $1'${Color_Off}"
      fi
    else

      echo -e -n "Do you want to stop the running $2? [${URed}Y${Color_Off}/n] "
      read -n 1 -r
      echo    # (optional) move to a new line
      # Default is yes
      if [[ ! $REPLY =~ ^[Nn]$ ]]
      then
        docker stop $1> $OUT
        echo -e "* Stopped the $2"
      else
        echo -e "* You can attach to the running container by typing '${Green}docker attach $1'${Color_Off}"
      fi
    fi
  fi
}


function delete_stopped_container() {
  # Arg 1 is the container_name
  # Arg 2 is the container_str with colors
  # eg: delete_stopped_container "$os_container_name" "$os_container_str"


  # if the container still exists but it is stopped, delete?
  if [ ! "$(docker ps -q -f name=$1)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$1)" ]; then
      # cleanup?
      echo -e "The $2 is stopped but still present"
      read -p "Do you want to delete the $1? [${URed}Y${Color_Off}/n] " -n 1 -r
      echo    # (optional) move to a new line
      # Default is yes
      if [[ ! $REPLY =~ ^[Nn]$ ]]
      then
        docker rm $1> $OUT
        echo -e "* Deleted the $2"
      fi
    fi
  fi
}

function delete_image() {
  # Arg 1 is the image_name
  # Arg 2 is the image_str with colors
  # Arg 3 is the linked container_name
  # Arg 4 is the default answer: pass Y for yes, N for no. Default N

  # eg: delete_image "$os_image_name" "$os_image_str" "$os_container_name" N

  # if the container still exists but it is stopped, delete?
 if [ ! "$(docker ps -aq -f name=$3)" ]; then
    if [[ $4 = Y ]]; then
      echo -e -n "Do you want to delete the $2? [${URed}Y${Color_Off}/n]? "
      read -n 1 -r
      echo    # (optional) move to a new line
      # Default is yes
      if [[ ! $REPLY =~ ^[Nn]$ ]]
      then
        docker rmi $1> $OUT
        echo -e "* Deleted the $2"
      fi
    else
      echo -e -n "Do you want to delete the $2? [y/${URed}N${Color_Off}]? "
      read -n 1 -r
      echo    # (optional) move to a new line
      # Default is no
      if [[ $REPLY =~ ^[Yy]$ ]]
      then
        docker rmi $1> $OUT
        echo -e "* Deleted the $2"
      fi

    fi

  fi
}



function cleanup() {

  # ARG 1 is the exit code, 0 for normal, 1 for ctrl_c
  echo
  echo "Cleaning up:"

  # If the container is still running, ask whether we stop it first
  #if [ "$(docker ps -q -f name=$os_container_name)" ]; then
    #echo -e -n "Do you want to stop the running $os_container_str? [${URed}Y${Color_Off}/n] "
    #read -n 1 -r
    #echo    # (optional) move to a new line
    ## Default is yes
    #if [[ ! $REPLY =~ ^[Nn]$ ]]
    #then
      #docker stop $os_container_name
    #else
      #echo -e "You can attach to the running container by typing '${Green}docker attach $os_container_name'${Color_Off}"
    #fi
  #fi

  # If the openstudio container is still running, stop it? Defaults to Yes
  stop_running_container "$os_container_name" "$os_container_str" Y

  # Note: We shouldn't get in there for the my_openstudio container really,
  # because I used --rm when 'run' so if you stop -> it's gone
  delete_stopped_container "$os_container_name" "$os_container_str"

  # Cleanup custom/openstudio image?
  delete_image "$os_image_name" "$os_image_str" "$os_container_name" N

  # Stop mongo? Defaults to No
  stop_running_container "$mongo_container_name" "$mongo_container_str" N


  if [[ $machine == Linux ]]; then
    echo
    echo -e "${On_Blue}Fixing ownership: setting it to user=$USER and chmod=664 (requires sudo)${Color_Off}"
    sudo chown -R $USER:$USER ./test/
    sudo find ./test/ -type f -exec chmod 664 {} \;
  fi

  exit $1

}


# trap ctrl-c and call cleanup()
trap cleanup INT




########################################################################################
#                               M O N G O
########################################################################################

mongo_ip=''

if [ "$use_mongo" = true ]; then
  if [ ! "$(docker ps -q -f name=$mongo_container_name)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$mongo_container_name)" ]; then
      # cleanup
      echo -e "* Deleting existing mongo $mongo_container_str"
      docker rm $mongo_container_name> $OUT
    fi
    # run your container
    # Have the mongo docker write to the local directory with -v
    echo -e "* Running mongo $mongo_container_str"
    # On Unix it seems to keep running with the -d option only
    # docker run --name $mongo_container_name -v "$(pwd)/database":/data/db -d $mongo_image_name > $OUT
    # On windows it doesn't because it doesn't run in the foreground, so here's a workaround
    docker run --name $mongo_container_name -v "$(pwd)/database":/data/db -d $mongo_image_name tail -f /dev/null > $OUT
  fi


  # Place the mongo container ip into a file, that'll get added to the openstudio container via the dockerfile
  # Actually we will set an environment variable in the dockerfile named MONGOIP too
  mongo_ip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $mongo_container_name`
  echo $mongo_ip > mongo_ip
fi

#docker run --name my_openstudio --link openstudio-mongo:mongo -d -ti --rm nrel/openstudio:2.2.1
#echo "Copying files to ${docker_id}"
#docker cp ./measures ${docker_id}:/var/simdata/openstudio/measures
#docker cp ./model ${docker_id}:/var/simdata/openstudio/model
#docker cp ./weatherdata ${docker_id}:/var/simdata/openstudio/weatherdata
#docker cp ./model_tests.rb ${docker_id}:/var/simdata/openstudio/model_tests.rb
#docker cp ./test.osw ${docker_id}:/var/simdata/openstudio/test.osw


#docker attach my_openstudio
#sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
#apt-get update
## cannot install mongodb-org, not sure why
#sudo apt-get install -y mongodb

#mongo 172.17.0.2


########################################################################################
#          B U I L D    O P E N S T U D I O    C U S T O M    I M A G E
########################################################################################

# We are going to use a Dockerfile to load the tagged nrel/openstudio image, then add some files, etc




# Prepare the dockerfile (string substitution in the template file)
sed -e "s/\${os_version}/$os_version/" -e "s/\${mongo_ip}/$mongo_ip/" Dockerfile.in > Dockerfile

echo ""
# If the docker image doesn't already exists
if [ -z $(docker images -q $os_image_name) ]; then
  # If the docker base nrel/openstudio:tag image doesn't already exists
  # Make sure the user wants to actually download it
  if [ -z $(docker images -q $base_os_image_name) ]; then
    echo -e "The docker base $base_os_image_str isn't on your disk. This may require downloading 1+ GB of data"
    echo -e -n "Are you sure you want to continue? [y/${URed}N${Color_Off}] "
    read -n 1 -r
    echo
    # Default is no
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Exiting program"
      exit 0
    fi
  fi

  echo -e "* Building the $os_image_str from Dockerfile"
  docker build $platform -t $os_image_name .

else
  echo -e "The docker $os_image_str already exists"
  echo -e -n "Do you want to force rebuild? [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    echo -e "* Rebuilding the image $os_image_str from Dockerfile"
    docker rmi $os_image_name > $OUT
    docker build $platform -t $os_image_name .
  fi
  echo
fi


# Execute a container in detached mode
# Check first if there is an existing one, and tell user what to do
if [ "$(docker ps -aq -f name=$os_container_name)" ]; then
  echo -e "Error: The $os_container_str is already running..."
  echo -e "stop it with '${Green}docker stop $os_container_name'${Color_Off}"
  echo -e "perhaps also run ${Green}'docker rm $os_container_name'${Color_Off}"
  exit 1
fi

echo -e "* Launching the $os_container_str"
if [ "$use_mongo" = true ]; then
  # Launch, with link to the mongo one
  docker run $platform --name $os_container_name --link $mongo_container_name:mongo -v `pwd`/test:/var/simdata/openstudio/OpenStudio-resources -d -it --rm $os_image_name /bin/bash > $OUT
else
  # docker run $platform --name $os_container_name -v `pwd`/test:/root/test -d -it --rm $os_image_name /bin/bash > $OUT
  docker run $platform --name $os_container_name -v `pwd`/test:/var/simdata/openstudio/OpenStudio-resources/test -d -it --rm $os_image_name /bin/bash > $OUT
fi

# Chmod execute the script
docker exec $os_container_name chmod +x docker_container_script.sh

if [ "$os_version" = 2.0.4 ]; then
  echo -e "${On_Red}CUSTOM WORKAROUND FOR BROKEN 2.0.4${Color_Off}"
  # This one has missing dependencies
  docker exec $os_container_name sudo apt update
  docker exec $os_container_name sudo apt install -y libglu1 libjpeg8 libfreetype6 libdbus-glib-1-2 libfontconfig1 libSM6 libXi6
  # Need to specifically require /usr/Ruby/openstudio instead of just openstudio
  docker exec $os_container_name sed -i "s:require 'openstudio':require '/usr/Ruby/openstudio':" model_tests.rb
  # Etc.nprocessor unknown, so replace with bash nproc
  docker exec $os_container_name sed -i "s/Etc.nprocessors/$(nproc)/" model_tests.rb
fi


# Execute it
# Launch the regression tests
echo -e -n "Do you want to launch the regression tests? [${URed}Y${Color_Off}/n] "
read -n 1 -r
echo    # (optional) move to a new line
# Default is yes
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
  echo "Do you want to pass a filter 'pattern' passed to '$test_file -n /pattern/'"
  echo "Leave empty for all tests, or input a pattern. Follow by [ENTER] in both cases"
  read filter
  echo -e "\nRunning docker_container_script.sh:"
  echo "------------------------------------"
  docker exec $os_container_name /bin/bash ./docker_container_script.sh $test_file $filter

fi


# Attach to the container
echo -e -n "Do you want to attach to the running $os_container_str? [${URed}Y${Color_Off}/n] "
read -n 1 -r
echo    # (optional) move to a new line
# Default is yes
if [[ ! $REPLY =~ ^[Nn]$ ]]
then
  if [[ "$(uname)" = MINGW* ]]; then
    winpty docker attach $os_container_name
  else
    docker attach $os_container_name
  fi
fi



# Run cleanup when normal execution
cleanup 0
