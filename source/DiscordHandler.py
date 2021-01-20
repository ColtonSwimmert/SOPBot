import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio
import json

class discordUserEvents():
    '''
    Base class to handle data about user added sound clips and images
    '''
    
    JSON_FILE_NAME = "testJsonFile.json"
    EventInfo = {} # make a dict for testing prior to having data already in json
    
    
    def __init__(self): # load data from json file. Update json while program is running
        
        if discordUserEvents.EventInfo != None: #constructor has already been run
            return
        
        
        try:
            jsonFile = open(self.JSON_FILE_NAME,"r")
            discordUserEvents.EventInfo = json.load(jsonFile)
            jsonFile.close()
        
            # for now
            discordUserEvents.EventInfo = {}
            
        except IOError:
            print("Warning json file not found. Creating new json file.")
            os.system("touch " + discordUserEvents.JSON_FILE_NAME)
            discordUserEvents.EventInfo = {}
        
        
    def cleanUp(self): # when bot is closed run this to save json.
        
        if discordUserEvents.EventInfo != None: # to prevent multiple dumps
            # after dumping json will set dictionary to none
            
            jsonFile = open(discordUserEvents.JSON_FILE_NAME,"w")            
            json.dumps(discordUserEvents.EventInfo)
            discordUserEvents.EventInfo = None
    
        
    def addEventINFO(self,fileINFO): # store metadata from image added
        
        # format of file INFO
        # format for data[fileName, fileEXT, AuthorID, AuthorName, date]
        fileFormat = ["extension","AuthorID","AuthorName","date"]
        
        
        # add unique name for file before appending data
        imageNameCounter = 1
        name = fileINFO[0].lower()

        
        # find the correct index for filename if name is already taken
        while(True):

                if name not in discordUserEvents.EventInfo: # add event to list
                    
                    discordUserEvents.EventInfo[name] = {}
                    break
                    
                name = name + str(imageNameCounter)
                imageNameCounter += 1
        
        
        # add additional information about event added
        index = 1
        for DataFormat in fileFormat:
            
            discordUserEvents.EventInfo[name][DataFormat] = fileINFO[index]
            index += 1
        
        # create directory if necessary 
        self.checkDirectory(fileINFO[1])
        
        
        # update name in list to be passed back
        fileINFO[0] = name
        
        
    def removeEventINFO(self, fileName): # remove an event
        
        # obtain the full filename of the file to be deleted
        fileEXT = discordUserEvents.EventInfo[fileName]["fileEXT"]
        fullName = fileName + "." + discordUserEvents.EventInfo[fileName]["fileEXT"]
        
        
        # move to the file directory and remove the file
        currentDirectory = os.getcwd()
        os.chdir("../Event_Files/" + fileEXT)
        
        
        # check if file exists
        if os.path.exists(fullName):
            os.remove(fileName)
        else:
            print("error file doesnt exist...")
        
        
        # go back to the original directory after deleting the file and update json dictionary
        os.chdir("../../source/")
        
    def loadEventInfo(self): # find info about an event
        pass
        
    def ifAuthor(self):
        pass
        
    def checkDirectory(self,fileEXT):
        # determine that the directory that contains this filetype exists. if not add it
        
        if not os.path.isdir("../Event_Files/" + fileEXT):
            # if this directory doesnt exist then make it
            os.mkdir("../Event_Files/" + fileEXT)
        
        

class discordReactions(discordUserEvents):
    '''
    Add user reactions and allow for accessing reactions from 
    Host's computer.
    Additional: Image modifications, distortions, gray scales, etc
    '''

    
    def __init__(self): # load reaction images from reaction directory
        self.imagePath = "../Event_Files/"
        self.commands = {}
        self.reactions = {}
        super().__init__()
        
    async def postReaction(self,message): 
        
        reactionName = message.content.lstrip(message.content[0])
        
        # if in reaction list then post
        if reactionName in discordUserEvents.EventInfo:
            
            fileEXT = discordUserEvents.EventInfo[reactionName]["extension"]
            myFile = discord.File(self.imagePath + fileEXT + "/" + reactionName + "." + fileEXT,filename=reactionName + "." + fileEXT)
            await message.channel.send(file=myFile)
        
        else:
            
            await message.channel.send(reactionName + " is not a valid reaction...")
        
        
    async def addReaction(self, message):
        
        # ensure there is an attachment 
        if message.attachments == None:
            await message.channel.send("No reaction provided.")
            return
        
        # obtain only the first attachment and its fileName
        eventAttachment = message.attachments[0]
        fileEXT = str(eventAttachment.filename.split(".")[1])
        
            
        # obtain fileName and EXT
        messageContent = message.content.split()
        
        
        # make sure that we are getting the filename
        contentLength = len(messageContent)
        fileName = messageContent
        
        if contentLength < 1:
            print(str(messageContent))
            await message.channel.send("Missing reaction name.")
            return
        
        if contentLength == 1 or contentLength > 1: # if more text is included afterwards
            fileName = messageContent[0]
        
        
        # format for data[fileName, fileEXT, AuthorID, AuthorName, date]
        eventInformation = []
        
        
        # append filename and ext
        eventInformation.append(fileName) #filename
        eventInformation.append(fileEXT)
        
        
        # append author information
        author = message.author
        
        eventInformation.append(author.id)
        eventInformation.append(author.name)
        eventInformation.append(str(datetime.now()))
        
        
        # send info to addEventINFO
        self.addEventINFO(eventInformation)
        
        
        # save file and display info to chat
        await eventAttachment.save(self.imagePath + fileEXT + "/" + eventInformation[0] + "." + eventInformation[1])
        
        # send message in chat
        await message.channel.send("Created new reaction <" + eventInformation[0] + "> Author: " + eventInformation[3] + " (" + eventInformation[4] + ")")
        
            
        
class discordSoundBoard(discordUserEvents): #bot will join and play the sound clip available
    
    def __init__(self):
        pass
     

class botPermission():
    '''
    prevent some us
    '''


class discordChat(): # handler for chat related functions

    # command
    commands = {}
    discordClient = None
    reactions = None
    
    def __init__(self, discordClient = None):
        
        self.discordClient = discordClient
        self.reactions = discordReactions() # testing
        
        self.commands = {
                "buzz" : self.tryBuzz,
                "wutface": self.displayWut,
                "addreaction": self.addReaction,
                "flip" : self.flipCoin
                }        
            
    async def tryBuzz(self,message):
        await message.channel.send("buzzing")
        buzzer.on()
        time.sleep(1)
        buzzer.off()   
    
     
    async def displayWut(self,message):
    
        await message.channel.send(file=discord.File('wutface.jpg'))
		
     
    async def addReaction(self,message):
        
        await self.reactions.addReaction(message)


    async def flipCoin(self,message):
    
        await message.channel.send("Flipping...")
        random.seed(datetime.now())
        coinVal = random.randint(0,1)
        output = ""
    
    
        time.sleep(1.5)
    
        if coinVal == 0:
            output = "Heads!"
        else:
            output = "Tails!"
        
        await message.channel.send(output)




