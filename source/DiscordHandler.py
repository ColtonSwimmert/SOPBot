import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio
import json
import youtube_dl
import discord

class discordUserEvents():
    '''
    Base class to handle data about user added sound clips and images
    '''
    
    JSON_FILE_NAME = "testJsonFile.json"
    EventInfo = None
    
    
    def __init__(self): # load data from json file. Update json while program is running
        
        if discordUserEvents.EventInfo != None: #constructor has already been run
            return
        
        try:
            jsonFile = open(self.JSON_FILE_NAME,"r")
            discordUserEvents.EventInfo = json.load(jsonFile)
            jsonFile.close()
            
        except (IOError, ValueError) as e:
            print("Warning json file not found. Creating new json file.")
            os.system("touch " + discordUserEvents.JSON_FILE_NAME)
            discordUserEvents.EventInfo = {}
        
        
    def cleanUp(self): # when bot is closed run this to save json.
        
        if discordUserEvents.EventInfo != None: # to prevent multiple dumps
            # after dumping json will set dictionary to none
            
            jsonFile = open(discordUserEvents.JSON_FILE_NAME,"w")            
            json.dump(discordUserEvents.EventInfo,jsonFile,indent=4)
            jsonFile.close()
            discordUserEvents.EventInfo = None
    
        
    def addEventINFO(self,fileINFO): # store metadata from image added
        
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
        event = discordUserEvents.EventInfo[fileName]
        fileEXT = event["extension"]
        fullName = fileName + "." + fileEXT
        
        
        # move to the file directory and remove the file
        #currentDirectory = os.getcwd()
        #os.chdir("../Event_Files/" + fileEXT)
        filePath = "../Event_Files/" + fileEXT + "/" + fullName
        
        # check if file exists
        if os.path.exists(filePath):
            os.remove(filePath)
        else:
            print("error file doesnt exist...")
        
        discordUserEvents.EventInfo.pop(fileName)
        
        # go back to the original directory after deleting the file and update json dictionary
        #os.chdir("../../source/")
        
    def loadEventInfo(self): # find info about an event
        pass

    def obtainAuthorInformation(self,message, container):

        #provide a container for the information

        author = message.author 
        
        container.append(author.id)
        container.append(author.name)
        container.append(str(datetime.now()))

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
        fileEXT = eventAttachment.filename.split(".")[1]
        
        
        # obtain fileName and EXT
        messageContent = message.content.split()
        
        
        # make sure that we are getting the filename
        contentLength = len(messageContent)
        
        if contentLength < 1:
            print(str(messageContent))
            await message.channel.send("Missing reaction name.")
            return
        
        
        fileName = messageContent[0]
        
        # format for data[fileName, fileEXT, AuthorID, AuthorName, date]
        eventInformation = []
        
        
        # append filename and ext
        eventInformation.append(fileName) #filename
        eventInformation.append(fileEXT)
        
        #obtain author info
        self.obtainAuthorInformation(message,eventInformation)
        
        
        # send info to addEventINFO
        self.addEventINFO(eventInformation)
        
        
        # save file and display info to chat
        await eventAttachment.save(self.imagePath + fileEXT + "/" + eventInformation[0] + "." + eventInformation[1])
        
        # send message in chat
        await message.channel.send("Created new reaction <" + eventInformation[0] + "> Author: " + eventInformation[3] + " (" + eventInformation[4] + ")")
        
        
    async def removeReaction(self,message):
        # get information about author before sending to remove event
        
        authorID = message.author.id
        fileName = message.content
        response = ""
        event = None
        
        try:
            event = discordUserEvents.EventInfo[fileName]
        
        except KeyError:
            await message.channel.send(fileName + " does not exist!")
            return
            
        
        if event["AuthorID"] == authorID:
            
            self.removeEventINFO(fileName)
            response = fileName + " has been removed!"
        
        else:
            response = "You are not the author of this reaction!"
        
        
        await message.channel.send(response)
            
        
class discordSoundBoard(discordUserEvents): #bot will join and play the sound clip available
    
    def __init__(self):
        
        self.queue = []
        self.soundPlaying = False
        self.mp3Path = "../Event_Files/mp3/"
        self.currentVoice = None
        

    async def playSound(self, message):
        
        self.queue.append(message.content) # add to queue

        if self.soundPlaying:     
            return

        self.soundPlaying = True # start playing sound
        channel = message.author.voice.channel
        self.currentVoice = await channel.connect()


        for sound in self.queue:
            soundName = sound.lstrip("!")

            #for clip in self.queue:
            soundFile = self.mp3Path + soundName + ".mp3"
            
            if not os.path.isfile(soundFile): # if file doesnt exist
                await message.channel.send(soundName + " not found!")
                continue


            self.currentVoice.play(discord.FFmpegPCMAudio(soundFile))

            while self.currentVoice.is_playing():
                await asyncio.sleep(1)
           
        # once done disconnect and set to None
        await self.currentVoice.disconnect()
        self.currentVoice = None
        self.soundPlaying = False
        self.queue.clear()


    async def stopSound(self,message):
        
        if self.soundPlaying:

            self.currentVoice.stop()
            await self.currentVoice.disconnect()
            self.currentVoice = None
            self.soundPlaying = False
            self.queue.clear()

    
    async def addClip(self,message):
        
        
        content = message.content.split(" ")[1:] # obtain youtubelink and name


        # downloads the clip 
        try:
            ydl_opts = {'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}], 'outtmpl' : content[1]}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([content[0]])
        
        except Exception:
            await message.channel.send("Unable to create event for <" + content[1] + ">")
            return


        # move mp3 to correct directory
        os.system("mv " + content[1] + ".mp3 " + self.mp3Path)


        # add author information to json
        eventInfo = []
        eventInfo.append(content[1])
        eventInfo.append(".mp3")
        self.obtainAuthorInformation(message,eventInfo)
        self.addEventINFO(eventInfo)

        # send message in chat
        await message.channel.send("Created new clip <" + eventInfo[0] + "> Author: " + eventInfo[3] + " (" + eventInfo[4] + ")")

    
    def downloadSoundClip(self,clipArgs): # obtain the mp3 for the soundclip
        
        ydl_opts = {'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}], 'outtmpl' : clipArgs[1]}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clipArgs[0]])
            

        eventInfo = []
        eventInfo.append(clipArgs[1])
        eventInfo.append("mp3")

        discordUserEvents.obtainAuthorInformation()
        

class discordChat(): # handler for chat related functions

    # command
    commands = {}
    discordClient = None
    reactions = None
    
    def __init__(self, discordClient = None):
        
        #handlers
        self.discordClient = discordClient
        self.reactions = discordReactions() # testing
        self.soundBoard = discordSoundBoard() #testing
        
        
        # members
        self.downloadThread = None
        
        
        self.commands = {
                "buzz" : self.tryBuzz,
                "addreaction" : self.addReaction,
                "removereaction" : self.removeReaction,
                "flip" : self.flipCoin
                }        
            
    async def tryBuzz(self,message):
        await message.channel.send("buzzing")
        buzzer.on()
        time.sleep(1)
        buzzer.off()   
		
     
    async def addReaction(self,message):
        
        await self.reactions.addReaction(message)


    async def removeReaction(self,message):
        
        await self.reactions.removeReaction(message)
        
        
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
