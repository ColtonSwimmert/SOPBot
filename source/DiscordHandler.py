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
        imageNameCounter = 0
        name = fileINFO[0].lower()
        tempName = name
        
            
        # find the correct index for filename if name is already taken
        while(True):
                
                if tempName not in discordUserEvents.EventInfo: # add event to list
                    
                    name = tempName
                    discordUserEvents.EventInfo[name] = {}
                    break
                    
                imageNameCounter += 1
                tempName = name + str(imageNameCounter)
        
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
        filePath = "../Event_Files/" + fileEXT + "/" + fullName
        
        # check if file exists
        if os.path.exists(filePath):
            os.remove(filePath)
        else:
            print("error file doesnt exist...")
        
        discordUserEvents.EventInfo.pop(fileName)
        

    def obtainAuthorInformation(self,message, container):

        #provide a container for the information
        author = message.author 
        
        container.append(author.id)
        container.append(author.name)
        container.append(str(datetime.now()))

    def isAuthor(self,message):

        try:
            if discordUserEvents.EventInfo[message.content]["AuthorID"] == message.author.id:
                return True
        
        except KeyError:
            pass

        return False
    
    def checkDirectory(self,fileEXT):
        # determine that the directory that contains this filetype exists. if not add it
        
        if not os.path.isdir("../Event_Files/" + fileEXT):
            # if this directory doesnt exist then make it
            os.mkdir("../Event_Files/" + fileEXT)


    @staticmethod
    async def aboutEvent(message):

        eventName = message.content
        eventDict = discordUserEvents.EventInfo

        if not eventName in eventDict:
            await asyncio.sleep(0) # do nothing
            return

        eventDict = eventDict[eventName]
        eventOutput = "```\n"
        eventOutput += "Event: " + eventName + "\n"
        eventOutput += "---------------------\n"

        eventOutput += "AuthorName: " + eventDict["AuthorName"] + "\n"
        eventOutput += "AuthorID: " + str(eventDict["AuthorID"]) + "\n"
        eventOutput += "Date: " + eventDict["date"] + "\n"

        eventOutput += "```"

        await message.channel.send(eventOutput)


    @staticmethod
    async def listEvents(message):

        fullList = "```\n"
        fullList += "SOPBOT EVENT COMMANDS\n"
        fullList += "---------------------\n"

        reactions = "Reaction(~): "
        soundboardClips = "SoundBoard($): "

        for key in discordUserEvents.EventInfo:
            
            if discordUserEvents.EventInfo[key]["extension"][0] == "m":

                soundboardClips += key + ", " 
            else:
                reactions += key + ", "
        
        
        fullList += reactions.rstrip(", ") + "\n\n"
        fullList += soundboardClips.rstrip(", ") + "\n"
        fullList += "```"

        await message.channel.send(fullList)


class discordReactions(discordUserEvents):
    '''
    Add user reactions and allow for accessing reactions from 
    Host's computer.
    Additional: Image modifications, distortions, gray scales, etc
    '''


    def __init__(self): # load reaction images from reaction directory
        self.imagePath = "../Event_Files/"
        self.reactions = {}
        self.commands = {
            "" : self.postReaction,
            "addreaction" : self.addReaction,
            "removereaction" : self.removeReaction
        }
        super().__init__()
        
    async def postReaction(self,message): 
        
        reactionName = message.content
        
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
        
        self.queue = [] # will swap to deque later
        self.downloadQueue = []
        self.isDownloading = False
        self.waitUntil = False
        self.soundPlaying = False
        self.mp3Path = "../Event_Files/mp3/"
        self.currentVoice = None
        self.waitTime = 120 # time until bot disconnects from VC


        self.commands = {
            "stopsound" : self.stopSound,
            "addclip" : self.addClip,
            "removeclip" : self.removeClip,
            "skip" : self.skip,
            "" : self.playSound
        }

        super().__init__()

    async def playSound(self, message):
        
        # append clip, return if already playing
        self.queue.append(message.content) # add to queue
        if self.soundPlaying:     
            return


        # determine if user is in a channel
        channel = message.author.voice.channel
        if channel == None:
            await message.channel.send("You are not in a voice channel!")
            return


        # connect and start playing 
        self.currentVoice = await channel.connect()
        self.soundPlaying = True 
        timerIndex = 0
        

        while(timerIndex < self.waitTime):

            # play sounds queued
            for sound in self.queue:

                timerIndex = 0
                soundName = sound.lower().lstrip("!")

                #for clip in self.queue:
                soundFile = self.mp3Path + soundName + ".mp3"
            

                if not os.path.isfile(soundFile): # if file doesnt exist
                    await message.channel.send(soundName + " not found!")
                    continue


                self.currentVoice.play(discord.FFmpegPCMAudio(soundFile))

                while self.currentVoice.is_playing():
                    await asyncio.sleep(1)
                    if self.soundPlaying == False:
                        return


            self.queue.clear() 
            await asyncio.sleep(1)
            timerIndex += 1

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

    async def skip(self,message):

        self.currentVoice.stop() # set sound to stop
        await asyncio.sleep(0) # do nothing

    async def addClip(self,message):

        self.downloadQueue.append(message)

        if self.isDownloading:
            return

        self.isDownloading = True

        for newClip in self.downloadQueue:
            self.waitUntil = True
            threadDownload = threading.Thread(target=asyncio.run,args=(self.downloadClip(newClip),))
            threadDownload.start()

            while(self.waitUntil):
                await asyncio.sleep(1)

            await message.channel.send(message.content)

        self.downloadQueue.clear()
        self.isDownloading = False


    async def downloadClip(self,message):
        
        content = message.content.split(" ") # obtain youtubelink and name
        content[1] = content[1].lower()

        # downloads the clip 
        try:
            ydl_opts = {'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}], 'outtmpl' : content[1]}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([content[0]])
        
        except Exception:
            #await message.channel.send("Unable to create event for <" + content[1] + ">")
            message.content = "Unable to create event for <" + content[1] + ">"
            self.waitUntil = False
            return

        originalName = content[1]

        # add author information to json
        eventInfo = []
        eventInfo.append(content[1])
        eventInfo.append("mp3")
        self.obtainAuthorInformation(message,eventInfo)
        self.addEventINFO(eventInfo)


        # move mp3 to correct directory
        #os.system("mv " + content[1] + ".mp3 " + self.mp3Path)
        fullName = originalName + ".mp3"
        

        # determine if giving a clip range
        try:
            startTime = self.formatClipTime(content[2])
            endTime = self.formatClipTime(content[3])

            command = "ffmpeg -i " + fullName + " -vn -acodec copy -ss "
            command += startTime
            command += " -to "
            command += endTime
            command += " temp.mp3"


            os.system(command) # create copy
            os.system("rm " + fullName) # remove original
            os.system("mv temp.mp3 " + self.mp3Path + eventInfo[0] + ".mp3")

        except Exception:
            os.system("mv " + fullName + " " + self.mp3Path + eventInfo[0] + ".mp3") # renames and moves to new directory
            await asyncio.sleep(0) # do nothing

        self.waitUntil = False
        #await message.channel.send("Created new clip <" + eventInfo[0] + "> Author: " + eventInfo[3] + " (" + eventInfo[4] + ")")
        message.content = "Created new clip <" + eventInfo[0] + "> Author: " + eventInfo[3] + " (" + eventInfo[4] + ")"
    
    async def removeClip(self,message):

        if not self.isAuthor(message):
            await asyncio.sleep(0)
            return

        self.removeEventINFO(message.content)

        await message.channel.send("Removed " + message.content + "!")


    def formatClipTime(self,providedTime):
        # format time provided to bot 
        

        #HH:MM:SS
        clipTimes = providedTime.split(":")
        timeCount = len(clipTimes) - 3 
        outputString = ""

        while(timeCount < 0):
            outputString += "00:"
            timeCount += 1
        
        for selectedTime in clipTimes:
            outputString += selectedTime + ":"

        outputString = outputString.rstrip(":")

        return outputString


class discordChat(): # handler for chat related functions

    # command
    commands = {}
    discordClient = None
    reactions = None
    
    def __init__(self, discordClient = None):
        
        #handlers
        self.discordClient = discordClient
        
        
        # members
        self.downloadThread = None
        
        
        self.commands = {
                "buzz" : self.tryBuzz,
                "flip" : self.flipCoin,
                "listevents" : discordUserEvents.listEvents,
                "aboutevent" : discordUserEvents.aboutEvent
                }    

    def cleanUp(self):

        pass # do nothing for now    
            

    async def tryBuzz(self,message):
        await message.channel.send("buzzing")
        buzzer.on()
        time.sleep(1)
        buzzer.off()   
        
        
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
