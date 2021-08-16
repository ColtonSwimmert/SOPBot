#!/usr/bin/python
import discord
import os
import json
import asyncio
from MinecraftHandler import *
from DiscordHandler import *
from SteamLobbyHandler import *


# timing import to test general runtime of functions for imrpovements
import timeit

class MyClient(discord.Client):
    
    def __init__(self):
        
        super().__init__()
        
        # prefix members
        self.prefix = "$OP "
        self.minecraftPrefix = "$OPCRAFT "
        self.reactionPrefix = "~"
        self.soundPrefix = "$"
        self.lobbyPrefix = "!"

        # handlers 
        self.handlers = {
             self.prefix : discordChat(self),
             self.minecraftPrefix : Minecraft(self),
             self.reactionPrefix : discordReactions(),
             self.soundPrefix : discordSoundBoard(),
             self.lobbyPrefix : SteamLobbyHandler(self)
            }

        self.firstTimeSetup()


    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        self.userID = self.user.id

    async def startCleanUP(self):
        # clean up all handlers prior to exit
        for key in self.handlers: 
            self.handlers[key].cleanUp()
        await self.logout()
        
    async def on_message(self, message):
        handler = None
        command = None
        
        if message.content.startswith("`close"):
            await self.startCleanUP()
            return

        
        # parse a command and send to proper handler
        for key in self.handlers:
            if message.content.startswith(key): 
                # command found
                
                message.content = message.content.lstrip(key)           
                handler = self.handlers[key]
                command = self.getCommand(message.content)
                break 
            
        if command == None: # if no command, do nothing
            await asyncio.sleep(0)
            return
        
        # send command
        if handler.commands.get(command,None) != None: # attempt to lookup function
            message.content = message.content.lstrip(command).lstrip() # strip command and any left over whitespace
            await handler.commands[command](message)
        elif handler.commands.get("",None) != None: 
            await handler.commands[""](message) # run default function
        else:
            await asyncio.sleep(0) # do nothing
        
    async def on_reaction_add(self,reaction,user):
        """
        When a reaction is added, follow pipeline for handling reaction
        currently only pass to LobbyHandler
        """
        message = reaction.message
        if user.id == self.userID:
            # reaction is placed by bot
            return

        # determine if the reaction is for a steam lobby
        lobbyHandler = self.handlers[self.lobbyPrefix]
        for steamLobbyID in lobbyHandler.lobbies:
            steamLobby = lobbyHandler.lobbies[steamLobbyID]
            if steamLobby.getMessageID() == message.id:
                steamID = lobbyHandler.accountLinks.get(str(user.id),None)
                if steamID == None:
                    await message.remove_reaction(steamLobby.thumbsUP, user)
                    await message.channel.send(user.mention + " your account is not linked!")
                elif steamLobby.players.get(steamID, 0) == 0:
                    steamLobby.addPlayer(steamID, user.display_name)

    # CLIENT HELPER FUNCTIONS
    def getCommand(self,content): # obtain the command string 
        commandString = ""
        for char in content:
            if char == " ":
                break
            commandString += char
        return commandString


    def firstTimeSetup(self):
        # check if these directories exist, if not then create them prior to running SOP
        curDir = os.getcwd()
        directories = ["Event_Files", "Game_Files", "Minecraft"]        
        for pathName in directories:
            path = curDir + "/../" + pathName
            if not os.path.isdir(path):
                print("Directory for " + pathName + " doesnt exist in base directory, creating path now.")
                os.mkdir(path)
            



########################################################################
# obtain botID and initialize client

idFile = open("botID.txt","r")
botID = idFile.read().rstrip('\n') # read id and remove '\n'
idFile.close()

client = MyClient()
client.run(botID)