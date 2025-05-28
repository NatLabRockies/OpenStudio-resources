#!/bin/bash

# This script will run regression tests for many earlier OpenStudio versions
# For a single & more interactive version use the CLI ./launch_docker.sh

# AUTHOR: Julien Marrec, julien@effibem.com, 2018

# Source the file that has the colors
source colors.sh

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

#######################################################################################
#                           H A R D C O D E D    A R G U M E N T S
########################################################################################

# All versions you want to run
# 2.0.4 is supported, but it's very broken, transition to 2.0.5 is likely going to just fail, so remove it
declare -a all_versions=(
  "2.0.5" "2.1.0" "2.1.1" "2.1.2" "2.2.0" "2.2.1" "2.2.2" "2.3.0" "2.3.1" "2.4.0" "2.4.1" "2.5.0"
  "2.5.1" "2.5.2" "2.6.0" "2.6.1" "2.7.0" "2.7.1" "2.8.0" "2.8.1" "2.9.0" "2.9.1"
  "3.0.0" "3.0.1" "3.1.0" "3.2.0" "3.2.1" "3.3.0" "3.4.0" "3.5.0" "3.5.1" "3.6.0" "3.6.1" "3.7.0" "3.8.0" "3.9.0"
)

# declare -a all_versions=("3.0.0" "3.0.1" "3.1.0")

#for os_version in "${all_versions[@]}"; do
#  /Applications/OpenStudio-${os_version}/bin/openstudio model_tests.rb -n /space_level_dsoa/
#done

# Do you want to ask the user to set these arguments?
# If false, will just use the hardcoded ones
ask_user=true

# If image custom/openstudio:$os_version already exists, do you want to force rebuild?
# Otherwise will use this one
force_rebuild=false

test_file="model_tests.rb"

# Test filter: passed as model_tests -n /$filter/
filter="space_level_dsoa"
# Run only osms tests: filter="_osm"

# Delete custom/openstudio:$os_version image after having used it?
delete_custom_image=false

# Delete the base image? nrel/openstudio:$os_version
delete_base_image=false

# verbosity/debug mode.
verbose=false

# Use mongo?
use_mongo=false

# Maximum number of cores
# Defaults to all
n_cores=`nproc`
# Defaults to all minus 2
# n_cores=$(($(nproc) - 2))

# Don't rerun tests if out.osw is already there and success?
# TODO: Implement
donot_rerun_if_success=false

#######################################################################################
#                       G L O B A L    U S E R    A R G U M E N T S
########################################################################################

if [ "$ask_user" = true ]; then

  echo -e -n "Do you want to force rebuild for the ${BRed}custom/openstudio${Color_Off} images? [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    force_rebuild=true
  fi

  echo -e "Which ${BCyan}ruby test file${Color_Off}  do you want to run?"
  echo -e "Leave empty for ${URed}model_tests.rb${Color_Off}, or input a pattern. Follow by [ENTER] in both cases"
  read test_file


  echo -e "Do you want to pass a ${BCyan}filter 'pattern'${Color_Off} passed to '$test_file -n /pattern/'"
  echo "Leave empty for all tests, or input a pattern. Follow by [ENTER] in both cases"
  read filter

  echo -e -n "Do you want to delete the ${BRed}custom/openstudio${Color_Off} images after use? [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    delete_custom_image=true
  fi

  echo -e -n "Do you want to delete the base ${BPurple}nrel/openstudio${Color_Off} images after use? [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    delete_base_image=true
  fi

  echo -e -n "Do you want to enable the ${BCyan}verbose (debug) mode${Color_Off}? [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    verbose=true
  fi

  echo -e -n "Do you want to limit the number of ${BRed}threads${Color_Off} available to docker? Current default is ${BRed}`nproc`${Color_Off} [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -n "Please enter number: "
    read n_cores
    # Ensure it is a number (float or int)
    while ! [[ "$n_cores" =~ ^[0-9.]+$ ]]; do
      echo "Please enter an actual number!"
      read n_cores
    done
  fi

  echo -e -n "Do you want to force NOT re-running tests were we already have an out.osw and it was successful? By default it will rerun them [y/${URed}N${Color_Off}] "
  read -n 1 -r
  echo    # (optional) move to a new line
  # Default is No
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    donot_rerun_if_success=true
  fi

  echo "Global options have been set as follows:"
  echo "-----------------------------------------"
  echo "force_rebuild=$force_rebuild"
  if [ -z $test_file ]; then
    echo "test_file defaulted to model_tests.rb"
    test_file="model_tests.rb"
  else
    echo "test_file=$test_file"
  fi
  if [ -z $filter ]; then
    echo "filter=NONE"
  else
    echo "filter=$filter"
  fi
  echo "delete_custom_image=$delete_custom_image"
  echo "delete_base_image=$delete_base_image"
  echo "verbose=$verbose"
  echo "n_cores=$n_cores"
  echo "donot_rerun_if_success=$donot_rerun_if_success"
  echo
fi


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
#                              S E T U P
########################################################################################

# Image/Container names
mongo_image_name=mongo
mongo_container_name=openstudio-mongo

os_container_name=my_openstudio

# String representation with colors
mongo_image_str="${BPurple}image${Color_Off} ${UPurple}$mongo_image_name${Color_Off}"
mongo_container_str="${BCyan}container${Color_Off} ${UCyan}$mongo_container_name${Color_Off}"
os_container_str="${BBlue}container${Color_Off} ${UBlue}$os_container_name${Color_Off}"

########################################################################################
#                               M O N G O
########################################################################################

mongo_ip=''

if [ "$use_mongo" = true ]; then
  if [ ! "$(docker ps -q -f name=$mongo_container_name)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$mongo_container_name)" ]; then
      # cleanup
      echo -e "* Deleting existing mongo $mongo_container_str"
      docker rm $mongo_container_name > $OUT
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
  echo "Mongo ip is $mongo_ip"
  echo $mongo_ip > mongo_ip
fi

for os_version in "${all_versions[@]}"; do

  base_os_image_name=nrel/openstudio:$os_version
  os_image_name=custom/openstudio:$os_version
  os_image_str="${BRed}image${Color_Off} ${URed}$os_image_name${Color_Off}"
  base_os_image_str="${BRed}image${Color_Off} ${URed}$base_os_image_name${Color_Off}"

  echo
  echo -e "${On_Red}---------------------------------------------------------------${Color_Off}"
  echo -e "${On_Red}              STARTING WITH A NEW VERSION: $os_version               ${Color_Off}"
  echo -e "${On_Red}---------------------------------------------------------------${Color_Off}"
  echo

  ########################################################################################
  #          B U I L D    O P E N S T U D I O    C U S T O M    I M A G E
  ########################################################################################

  # We are going to use a Dockerfile to load the tagged nrel/openstudio image, then add some files, etc


  # Prepare the dockerfile (string substitution in the template file)
  sed -e "s/\${os_version}/$os_version/" -e "s/\${mongo_ip}/$mongo_ip/" Dockerfile.in > Dockerfile

  echo ""
  # If the docker image doesn't already exists
  if [ -z $(docker images -q $os_image_name) ]; then
    echo -e "* Building the $os_image_str from Dockerfile"
    docker build $platform -t $os_image_name .
  else
    if [ "$force_rebuild" = true ];
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
    echo -e "Warning: The $os_container_str is already running... Stopping"
    docker stop $os_container_name > $OUT
  fi

  echo -e "* Launching the $os_container_str"
  if [ "$use_mongo" = true ]; then
    # Launch, with link to the mongo one
    docker run $platform --name $os_container_name --cpus="$n_cores" --link $mongo_container_name:mongo -v `pwd`/test:/var/simdata/openstudio/OpenStudio-resources/test -d -it --rm $os_image_name /bin/bash > $OUT
  else
    docker run $platform --name $os_container_name --cpus="$n_cores" -v `pwd`/test:/var/simdata/openstudio/OpenStudio-resources/test -d -it --rm $os_image_name /bin/bash > $OUT
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
    # Etc.nprocessor unknown, replace with bash nproc
    docker exec $os_container_name sed -i "s/Etc.nprocessors/$(nproc)/" model_tests.rb
  fi
  # Execute it
  # Launch the regression tests
  docker exec $os_container_name /bin/bash ./docker_container_script.sh $test_file $filter


  # Clean up

  # Stop the os container, which is needed because I don't use run -rm, nor I attach to it
  if [ "$(docker ps -q -f name=$os_container_name)" ]; then
    docker stop $os_container_name > $OUT
    echo -e "* Stopped the $os_container_str"
  fi
  # if the container still exists but it is stopped, delete
  if [ ! "$(docker ps -q -f name=$os_container_name)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=$os_container_name)" ]; then
      docker rm $os_container_name > $OUT
      echo -e "* Deleted the $os_container_str"
    fi
  fi

  # Delete custom/openstudio:$os_version image?
  if [ "$delete_custom_image" = true ]; then
    docker rmi $os_image_name > $OUT
    echo -e "* Deleted the $os_image_str"
  fi

  # Delete base nrel/openstudio:$os_version image?
  if [ "$delete_base_image" = true ]; then
    docker rmi $base_os_image_name > $OUT
    echo -e "* Deleted the $base_os_image_str"
  fi

done

# On other Linux only, fix permissions
if [[ $machine == Linux ]]; then
  echo
  echo -e "${On_Blue}Fixing ownership: setting it to user=$USER and chmod=664 (requires sudo)${Color_Off}"
  sudo chown -R $USER *
  sudo find ./test/ -type f -exec chmod 664 {} \;
fi

# Stop the mongo one
docker stop $mongo_container_name > $OUT
echo -e "* Stopped the $mongo_container_str"
