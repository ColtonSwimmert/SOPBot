#!/bin/bash


worldName = $1 # pass the new world name 
spigotVersion = $2 # pass the curret spigot version we will use
currentDirectory = $(PWD) # obtain currentDirectory to come back after generating world


# create new world's directory
newWorldDirectory = "../Minecraft/$worldName/"
mkdir "$newWorldDirectory"

#copy contents of currentDirectory to new Directory then build 
cp "BuildTools.jar $newWorldDirectory"
cd "$newWorldDirectory" 


java -Xmx1024M -jar BuildTools.jar --rev spigotVersion


echo "Successfully built new world: $worldName"
