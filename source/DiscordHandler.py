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

    def isAuthor(self,authorID):

        try:
            if discordUserEvents.EventInfo[message.content]["AuthorID"] == authorID:
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

    async def changeName(self,message):
        pass
        '''
        if self.isAuthor(message.author.id):
            
            names = message.content.split(' ')

            try:
        '''



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

            if fileEXT == ".mp3":
                return

            myFile = discord.File(self.imagePath + fileEXT + "/" + reactionName + "." + fileEXT,filename=reactionName + "." + fileEXT)
            await message.channel.send(file=myFile)
        
        
        return
        
        
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
            response = "You are not the author!"
        
        
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
        
        # determine if clip exists
        if message.content not in discordUserEvents.EventInfo:
            return


        # append clip, return if already playing
        self.queue.append(message.content) # add to queue
        if self.soundPlaying:     
            return


        # determine if user is in a channel
        channel = message.author.voice
        if channel == None:
            await message.channel.send("You are not in a voice channel!")
            return


        # connect and start playing 
        self.currentVoice = await channel.channel.connect()
        self.soundPlaying = True 
        timerIndex = 0
        

        while(timerIndex < self.waitTime):

            # play sounds queued
            for sound in self.queue:

                timerIndex = 0
                soundName = sound.lower().lstrip("!")

                #for clip in self.queue:
                soundFile = self.mp3Path + soundName + ".mp3"
            

                # check if file exists, if not then it was probably removed by host so remove it from event list
                if not os.path.isfile(soundFile): 
                    await message.channel.send(soundName + " not found!")
                    self.removeEventINFO(soundName) # remove from listing
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
        
        content = message.content.split(" ") # obtain youtubelink and name\

        # downloads the clip 
        try:
            content[1] = content[1].lower()
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

        if not self.isAuthor(message.author.id):
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
        
        outputString += providedTime

        return outputString
        

class discordChat(): # handler for chat related functions

    # command
    commands = {}
    discordClient = None
    reactions = None
    

    def __init__(self, discordClient = None):
        
        #handlers
        self.discordClient = discordClient
        
        
        self.commands = {
                "listevents" : discordUserEvents.listEvents,
                "aboutevent" : discordUserEvents.aboutEvent,
                "cleanitup" : self.cleanChat,
                "timeout" : self.timeout,
                "timeoutremaining": self.timeOutRemaining
                }    

        #timeout helpers
        self.timeoutList = {}
        self.timeoutRunning = False


    def cleanUp(self):

        del self.timeoutList # clear timeout list


    async def cleanChat(self, message):

        purgeCount = int(message.content) + 1 #additional to remove the clean call
        await message.channel.purge(limit=purgeCount)


    async def timeout(self,message): # timeout a user from all vcs

        try:
            userID = message.author.id
            targetID = message.mentions[0]
            time_out_time = int(message.content.split(" ")[1])
        except Exception:
            #targetID doesnt exist
            asyncio.sleep(0)
            return

        if int(userID) != 140564870545408000: 
            await message.channel.send("cannot run this command!")
            return
                 
        # if already in list
        if targetID in self.timeoutList:
            asyncio.sleep(0) # do nothing
            return 

        self.timeoutList[targetID] = [targetID ,time_out_time,0] # message itself, the time to be in timeout, counter
        if self.timeoutRunning:
            asyncio.sleep(0)
            return

        while(True): # loop until everyone in timeout out of their timeout

            for target in self.timeoutList: # iterate through all users in timeout
                this = self.timeoutList[target]

                if this[0].voice != None:
                    await targetID.edit(voice_channel=None)

                if this[2] < this[1]:
                    this[2] = this[2] + 1

                else: # remove this user from timeout list
                    del self.timeoutList[target]

                if len(self.timeoutList) == 0: # list empty return
                    await asyncio.sleep(0)
                    self.timeoutRunning = False
                    return

            await asyncio.sleep(1)

    
    async def timeOutRemaining(self,message):
        userID = message.author.id

        if userID in self.timeoutList:
            this = self.timeoutList[userID]
            thisRemaining = str(this[2] - this[1])
            await message.channel.send("You have " + thisRemaining + " more seconds of timeout!")

        else:
            await message.channel.send("You are not on timeout")
