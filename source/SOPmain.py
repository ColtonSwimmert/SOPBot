#!/usr/bin/python
import discord
import os
import json
import asyncio
from MinecraftHandler import *
from DiscordHandler import *
from SteamLobbyHandler import *


class MyClient(discord.Client):
    
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        
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

    async def startCleanUP(self):
        # clean up all handlers prior to exit
        for key in self.handlers: 
            self.handlers[key].cleanUp()
        print("SOP going offline")
        await self.logout()
        
    async def on_message(self, message):
        handler = None
        command = None
        print(str(message.author.id))
        # putting this here for now until I find a better place to put
        if message.content.startswith("`close") and str(message.author.id) == "140564870545408000":
            await self.startCleanUP()
            return

        # parse a command and send to proper handler
        for key in self.handlers:
            if message.content.startswith(key): 
                # command found
                message.content = message.content.replace(key, "")              
                handler = self.handlers[key]
                command = self.getCommand(message.content)
                break 
            
        if command == None: # if no command, do nothing
            await asyncio.sleep(0)
            return

        # send command
        if handler.commands.get(command,None) != None: # attempt to lookup function
            message.content = message.content.replace(command + " ", "")
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
        
        # determine if the reaction is for a steam lobby
        lobbyHandler = self.handlers[self.lobbyPrefix]
        for steamLobbyID in lobbyHandler.lobbies:
            steamLobby = lobbyHandler.lobbies[steamLobbyID]
            if steamLobby.getMessageID() == message.id:
                # reaction is for a lobby handled
                steamID = lobbyHandler.accountLinks.get(user.id,None)
                if steamID == None:
                    # account is currently not linked, print so and remove reaction
                    await reaction.remove_reaction(steamLobby.thumbsUP, user)
                    await message.channel.send(user.mention + " your account is not linked!")
                else:
                    steamLobby.addPlayer(steamID, user.name)

    # CLIENT HELPER FUNCTIONS
    def getCommand(self,content): # obtain the command string 
        commandString = ""
        for char in content:
            if char == " ":
                break
            commandString += char
        return commandString


########################################################################
# obtain botID and initialize client

idFile = open("botID.txt","r")
botID = idFile.read().rstrip('\n') # read id and remove '\n'
idFile.close()

client = MyClient()
client.run(botID)