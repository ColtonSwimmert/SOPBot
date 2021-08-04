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


# HELPER FUNCTIONS

def contentSplit(string,splitCount=1):

    stringList = []

    string += " " # append empty char
    newString = ""
    stringCount = 0
    for char in string:
        if char == " ":
            stringList.append(newString)
            newString = ""
            stringCount += 1
            if stringCount == splitCount:
                return stringList
        else:
            newString += char

    return stringList

# Handler Classes
class discordUserEvents():
    '''
    Base class to handle data about user added sound clips and images
    '''
    
    JSON_FILE_NAME = "testJsonFile.json"
    EventInfo = None
    messageLength = 1970
    reactionMessages = []
    soundMessages = []
    fileFormat = ["extension","AuthorID","AuthorName","date", "source"]
    
    def __init__(self): # load data from json file. Update json while program is running
        
        if discordUserEvents.EventInfo != None: #constructor has already been run
            return
        
        try:
            jsonFile = open(self.JSON_FILE_NAME,"r")
            discordUserEvents.EventInfo = json.load(jsonFile)
            jsonFile.close()
            
        except (IOError, ValueError) as e:
            print("Warning json file not found. Creating new json file.")
            userEventsFile = open(discordUserEvents.JSON_FILE_NAME, "w")
            userEventsFile.close()
            discordUserEvents.EventInfo = {}
        
        self.eventPath = "../Event_Files/"

        # validate Event files and remove events stored in json that dont exist in directory
        eventDirectories = os.listdir(self.eventPath)
        validationDictionary = discordUserEvents.EventInfo.copy()
        for directory in eventDirectories:
            # go through event directories and determine if valid 
            formatEvents = os.listdir(self.eventPath + directory)
            for event in formatEvents:
                eventName = event.split(".")[0]
                if validationDictionary.get(eventName,None) == None:
                    # event is in the Dictionary
                    print("Deleting file " + eventName + " due to invalidation.")

        # generate intial messages for reactions/soundboard clips

        defaultReactionMessage = "```\n"
        defaultReactionMessage += "SOPBOT REACTION COMMANDS\n"
        defaultReactionMessage += "---------------------\n"
        reactionMessage = defaultReactionMessage
        reactionLength = len(defaultReactionMessage)


        defaultSoundMessage = "```\n"
        defaultSoundMessage += "SOPBOT SOUNDBOARD COMMANDS\n"
        defaultSoundMessage += "---------------------\n"
        soundBoardMessage = defaultSoundMessage
        soundLength = len(defaultSoundMessage)
        mp3Extension = "mp3"

        for event in discordUserEvents.EventInfo:
            charLength = len(event)

            if discordUserEvents.EventInfo[event]["extension"] == mp3Extension:
                if soundLength + charLength < discordUserEvents.messageLength:
                    soundBoardMessage += event + ", "
                    soundLength += charLength + 2
                else:
                    soundBoardMessage = soundBoardMessage.rstrip(", ")
                    soundBoardMessage += "```" # trailing message block
                    soundMessages.append([soundBoardMessage,soundLength])
                    soundLength = 0
                    soundBoardMessage = defaultSoundMessage
            else:
                if reactionLength + charLength < discordUserEvents.messageLength:
                    reactionMessage += event + ", "
                    reactionLength += charLength + 2
                else:
                    # append to message list and set values back to default
                    reactionMessage = reactionMessage.rstrip(", ")
                    reactionMessage += "```"
                    discordUserEvents.reactionMessages.append([reactionMessage,reactionLength])
                    reactionLength = 0
                    reactionMessage = defaultReactionMessage

        # add remaining to list
        reactionMessage += "```"
        soundBoardMessage += "```"
        discordUserEvents.reactionMessages.append([reactionMessage,reactionLength])
        discordUserEvents.soundMessages.append([soundBoardMessage,soundLength])
        
    def cleanUp(self): # when bot is closed run this to save json.
        
        if discordUserEvents.EventInfo != None: # to prevent multiple dumps
            # after dumping json will set dictionary to none
            
            jsonFile = open(discordUserEvents.JSON_FILE_NAME,"w")            
            json.dump(discordUserEvents.EventInfo,jsonFile,indent=4)
            jsonFile.close()
            discordUserEvents.EventInfo = None
    
        
    def addEventINFO(self,fileINFO): # store metadata from image added
        # format for data[fileName, fileEXT, AuthorID, AuthorName, date, source]
        
        # add unique name for file before appending data
        name = discordUserEvents.updateName(fileINFO[0].lower())
        
        # add additional information about event added
        index = 1
        for DataFormat in discordUserEvents.fileFormat:
            
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
            print("Error, file doesnt exist.")
        
        discordUserEvents.EventInfo.pop(fileName)
        

    def obtainAuthorInformation(self,message, container):

        #provide a container for the information
        author = message.author 
        
        container.append(author.id)
        container.append(author.name)
        container.append(str(datetime.now()))

    def isAuthor(self,authorID,filename):

        author = discordUserEvents.EventInfo.get(filename,None)
        if author != None:
            if author["AuthorID"] == authorID:
                return True
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
    async def listReactions(message):
        await message.channel.send(str(discordUserEvents.reactionMessages[0][0]))

    @staticmethod
    async def listSounds(message):
        await message.channel.send(str(discordUserEvents.soundMessages[0][0]))

    @staticmethod
    def updateName(newName):

        imageNameCounter = 0
        tempName = newName
        # find the correct index for filename if name is already taken
        while(True):
                
            if discordUserEvents.EventInfo.get(tempName,None) == None: # add event to list
                    
                name = tempName
                discordUserEvents.EventInfo[name] = {}
                break
                                        
            imageNameCounter += 1
            tempName = newName + str(imageNameCounter)
                
        return tempName

    async def changeName(self,message):
        messageContent = contentSplit(message.content,2)
        
        if len(messageContent) < 2:
            await message.channel.send("Missing arguments ex/ $changename <original> <new>")
            return
        
        originalName = messageContent[0].lower()
        newName = messageContent[1].lower()

        if not self.isAuthor(message.author.id,originalName):
            # if user is not author then terminate
            await message.channel.send("You are not the Author of " + originalName)
            return
            
        if discordUserEvents.EventInfo.get(newName,None) != None:
            newName = discordUserEvents.updateName(newName)
            
        discordUserEvents.EventInfo[newName] = discordUserEvents.EventInfo.pop(originalName)
        selectedEvent = discordUserEvents.EventInfo[newName]
        extension = selectedEvent["extension"]
        extPath = self.eventPath + extension + "/"

        originalFull = extPath + originalName + "." + extension + " " # extra space added for string padding
        newFull = extPath + newName + "." + extension

        os.system("mv " + originalFull + newFull)
        await message.channel.send("Event change to " + newName)

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
            "removereaction" : self.removeReaction,
            "changename" : self.changeName
        }
        super().__init__()
        
    async def postReaction(self,message): 
        reactionName = message.content
        # if in reaction list then post
        if discordUserEvents.EventInfo.get(reactionName,None) != None:
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
        eventInformation.append("Message Attachment")

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
        

        event = discordUserEvents.EventInfo.get(fileName,None)

        if event == None:
            await message.channel.send(fileName + "does not exist!")
            return

        
        if event["AuthorID"] == authorID:
            
            self.removeEventINFO(fileName)
            response = fileName + " has been removed!"
        
        else:
            response = "You are not the author!"
        await message.channel.send(response)
    
    def retrieveFilePath(self,name):
        image = discordUserEvents.EventInfo.get(name,None)
        if image == None or image["extension"][0:2] == "mp":
            # return none if doesnt exist or is an mp3/4 file
            return None , None
        return self.imagePath + image["extension"] + "/" + name + "." + image["extension"], name + "." + image["extension"]
            
        
class discordSoundBoard(discordUserEvents): #bot will join and play the sound clip available
    
    def __init__(self):
        
        self.queue = [] # will swap to deque later
        self.downloadQueue = []
        self.isDownloading = False
        self.waitUntil = False
        self.soundPlaying = False
        self.mp3Path = "../Event_Files/mp3/"
        self.eventPath = "../Event_Files/"
        self.currentVoice = None
        self.waitTime = 120 # time until bot disconnects from VC


        self.commands = {
            "" : self.playSound,
            "stopsound" : self.stopSound,
            "addclip" : self.addClip,
            "removeclip" : self.removeClip,
            "skip" : self.skip,
            "changename" : self.changeName,
            "source" : self.source,
        }

        super().__init__()

    async def playSound(self, message):
        
        # determine if clip exists
        if discordUserEvents.EventInfo.get(message.content,None) == None:
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
                soundName = sound.lower()

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
    
    async def source(self,message):
        # display the source of the sound clip.
        # if source is only part of video then show the start and end time
        content = message.content.rstrip()

        if discordUserEvents.EventInfo.get(content, None) == None:
            # event does not exist
            await message.channel.send("Event does not exist.")
            return

        source = discordUserEvents.EventInfo[content].get("source", None) 
        if source == None:
            await message.channel.send("Source is not provided")
            return

        await message.channel.send(source)

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

            # note: need to look into asyncio.get_event_loop() function to improve 
            # performance of this instead of busywaiting
            threadDownload = threading.Thread(target=asyncio.run,args=(self.downloadClip(newClip),))
            threadDownload.start()

            while(self.waitUntil):
                await asyncio.sleep(1)

            await newClip.channel.send(newClip.content)

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
        eventInfo.append(content[0]) # add link to source material
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
        message.content = "Created new clip <" + eventInfo[0].lower() + "> Author: " + eventInfo[3] + " (" + eventInfo[4] + ")"
    
    async def removeClip(self,message):

        if not self.isAuthor(message.author.id):
            await message.channel.send("You are not the author of this event!")
            return
        
        if message.content.rstrip() in self.queue:
            await message.channel.send("Cannot remove a clip that is currently being played!")
            return

        self.removeEventINFO(message.content)

        await message.channel.send("Removed " + message.content + "!")

    async def changeName(self,message):
        
        if not self.soundPlaying:
            await super().changeName(message)
        
        else:
            await message.channel.send("Cannot sound clips while currently playing sounds")


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
                "" : self.default,
                "commands" : self.commands, 
                "manual" : self.manual,
                "listreactions" : discordUserEvents.listReactions,
                "listsounds" : discordUserEvents.listSounds,
                "aboutevent" : discordUserEvents.aboutEvent,
                "cleanitup" : self.cleanChat,
                "timeout" : self.timeout,
                "timeoutremaining": self.timeOutRemaining
                }    

        #timeout helpers
        self.timeoutList = {}
        self.timeoutRunning = False

        # command usage dictionary
        self.usageDict = None
        try:
            commandFile = open("usage.json", "r")
            self.usageDict = json.load(commandFile)
        except IOError:
            print("Error loading command usage file. Renamed or does not exist?")

    def default(self):
        pass

    def cleanUp(self):
        del self.timeoutList # clear timeout list

    async def cleanChat(self, message):

        purgeCount = int(message.content) + 1 #additional to remove the clean call
        await message.channel.purge(limit=purgeCount)


    async def timeout(self,message): # timeout a user from all vcs
        # note: need to change this functionality since it can eat up some process time
        # potentially scrap this 

        try:
            userID = message.author.id
            targetID = message.mentions[0]
            time_out_time = int(message.content.split(" ")[1])
        except Exception:
            #targetID doesnt exist
            await asyncio.sleep(0)
            return
                 
        # if already in list
        if targetID in self.timeoutList:
            await asyncio.sleep(0) # do nothing
            return 

        self.timeoutList[targetID] = [targetID ,time_out_time,0] # message itself, the time to be in timeout, counter
        if self.timeoutRunning:
            await asyncio.sleep(0)
            return

        while(True): # loop until everyone in timeout out of their timeout
            removeList = []
            
            for target in self.timeoutList: # iterate through all users in timeout
                this = self.timeoutList[target]

                if this[0].voice != None:
                    await targetID.edit(voice_channel=None)

                if this[2] < this[1]:
                    this[2] = this[2] + 1

                else: # remove this user from timeout list
                    removeList.append(this)

            for removeable in removeList:
                self.timeoutList.pop(removeable)

            if len(self.timeoutList) == 0: # list empty return
                    await asyncio.sleep(0)
                    self.timeoutRunning = False
                    return

            await asyncio.sleep(1)

    
    async def timeOutRemaining(self,message):
        # NOTE: Needs to be updated or removed.
        userID = message.author.id

        if userID in self.timeoutList:
            this = self.timeoutList[userID]
            thisRemaining = str(this[2] - this[1])
            await message.channel.send("You have " + thisRemaining + " more seconds of timeout!")

        else:
            await message.channel.send("You are not on timeout")

    async def commands(self,message):
        ''' 
        Retreive all commands available from myClient class and 
        display for user
        '''
        handlerDict = self.discordClient.handlers
        commandMessage = "```\n"
        spacing = "\n\n"
        for prefix in handlerDict:
            handler = handlerDict[prefix]
            # retreive that handlers commands and label with its prefix 
            commandMessage += "(" + prefix.rstrip() + ") " 
            for command in handler.commands:
                if command == "":
                    continue

                commandMessage += command + ", "
            commandMessage = commandMessage.rstrip(", ") # remove ending seperator
            commandMessage += spacing

        commandMessage.rstrip(spacing)
        commandMessage += "\n```"

        await message.channel.send(commandMessage)

    async def manual(self, message):
        if self.usageDict == None:
            await message.channel.send("Error! Command manual missing from host.")
            return
        key = message.content.split()[0].lower()
        try:
            commandINFO = self.usageDict[key]
            await message.channel.send(commandINFO)
        except KeyError:
            await message.channel.send("Command does not exist.")