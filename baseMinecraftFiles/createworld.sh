#!/bin/bash

worldName=$1 # pass the new world name 
spigotVersion=$2 # pass the curret spigot version we will use
originalDirectory=$(pwd) # obtain currentDirectory to come back after generating world


# create new world's directory
newWorldDirectory="../Minecraft/$worldName/"
mkdir "$newWorldDirectory"


#copy contents of currentDirectory to new Directory then build 
cd "$newWorldDirectory"
cp "$originalDirectory/BuildTools.jar" "$newWorldDirectory/"

#generate the new world and remove unecessary file in directory.
java -Xmx1024M -jar BuildTools.jar --rev "$spigotVersion"
rm "$newWorldDirectory/BuildTools.jar"

# return to the original Directory
cd "$originalDirectory"
echo "Successfully built new world: $worldName"
