
import discord
import random
import threading
import time
from datetime import datetime
import os
import subprocess
import asyncio
import json
import re
import requests


class SteamLobbyHandler():

    def __init__(self,discordClient = None):        
        # Create Dictionary for Games that this Server will usually play



        # change to SOPmain to taking in these params
        try:    
            self.gamesFile = open("steamGames.json", "r")
            self.gamesList = json.load(self.gamesFile)
            self.gamesFile.close()

        except (IOError,ValueError) as e:

            print("Warning Json File containing steam games is not found!")
            print("Creating new json file \"steamGames.json\"")
            steamGamesFile = open("steamGames.json", "w")
            self.gamesList = {}
            steamGamesFile.write(str(self.gamesList))
            steamGamesFile.close()

        try:
            self.accountLinksFile = open("steamUsers.json", "r")
            self.accountLinks = json.load(self.accountLinksFile)
            self.accountLinksFile.close()

        except (IOError,ValueError) as e:
            accountsFile = open("steamUsers.json", "w")
            self.accountLinks = {}
            accountsFile.write(str(self.accountLinks))
            accountsFile.close()




        # Handler commands
        self.commands = {
            "" : self.default,
            "lobby" : self.createLobby,
            "host" : self.hostLobby,
            "embed" : self.embedLobby,
            "openlobbies" : self.displayOpenLobbies,
            "link" : self.linkAccount,
            "close" : self.closeLobby,
            "note" : self.addNote,
            "image" : self.addImage
        }

        # helper vars
        self.client = discordClient
        self.steamURL = "https://store.steampowered.com/app/"
        self.lookUpUrl = "https://steamid.io/lookup/"
        self.profileLookUp = "http://steamcommunity.com/profiles/"
        self.lobbies = {} #key creatorID, value steamLobby Class
        self.thumbsUP = "👍"

        # lobby tracker vars
        self.lobbyMessage = None
        self.lobbyThumbNail = "junyaTHUMB.jpg"

    async def default(self,message):
        pass

    def cleanUp(self):
        # dump newly acquired information to json files
        # dump discord/steam account links
        accountsFile = open("steamUsers.json", "w")            
        json.dump(self.accountLinks,accountsFile,indent=4)
        accountsFile.close()
        
        # dump steam games information
        steamGamesFile = open("steamGames.json", "w")
        json.dump(self.gamesList,steamGamesFile,indent=4)
        steamGamesFile.close()

    async def retreiveGameDetails(self,steamID):
        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text).group(0).rstrip("\" ")
        if lobbyLink != None:
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send("Error getting link")
            return

        # index 2 : appID, index 3: lobbyID
        gameDetails = re.split("[/]+", lobbyLink)  

        # check if games data is already stored
        if self.gamesList.get(gameDetails[2],None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error id")
                return

    async def createLobby(self, message):

        host = message.author
        hostID = str(host.id)
        
        # retreive user from steam links
        steamID = self.accountLinks.get(hostID,None)
        if steamID == None:
            await message.channel.send(host.mention + " Your account is not linked! Use !link <steam url> to link your account.")
            return

        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            await message.channel.send(host.mention + " Unable to retreive lobby information.")
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text)
        if lobbyLink != None:
            # need to update later
            lobbyLink = lobbyLink.group(0).rstrip("\" ")
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send(host.mention + " Could not retreive lobby, ensure that the lobby is joinable or you are not set to private.")
            return
        
        # retreive appID
        appID = re.split("[/]+", lobbyLink)[2]

        # check if games data is already stored
        game = self.gamesList.get(appID,None)
        if game == None:
            if not self.addGame(appID):
                print("Unable to add game data to SOPBot")
                return
        
        embeddedMessage = self.generateEmbedMessage(appID, host, lobbyLink)
        await message.channel.send(embed=embeddedMessage)


    async def hostLobby(self, message):
        # check if this user already has a lobby open

        host = message.author
        hostID = str(host.id)
        lobby = self.lobbies.get(hostID,None)

        if lobby != None:
            # this needs refactoring but currently works fine
            if lobby.imageName == None:
                tempPointer = await lobby.originalMessage.channel.send(embed=lobby.messageEmbed) 
                try:
                    await lobby.originalMessage.delete()
                except Exception:
                    print(lobby.hostName + "'s lobby message already deleted")
                await tempPointer.add_reaction(self.thumbsUP)
                lobby.originalMessage = tempPointer
            elif lobby.imagePath == None and lobby.imageName != None:
                tempPointer = await lobby.originalMessage.channel.send(embed=lobby.messageEmbed)
                try:
                    await lobby.originalMessage.delete()
                except Exception:
                    print(lobby.hostName + "'s lobby message already deleted")
                await tempPointer.add_reaction(self.thumbsUP)
                lobby.originalMessage = tempPointer
            else:
                # include display image and resend lobby embed
                imageFile = discord.File(lobby.imagePath, filename=lobby.imageName)
                lobby.messageEmbed.set_image(url="attachment://" + lobby.imageName)
                tempPointer = await lobby.originalMessage.channel.send(file=imageFile,embed=lobby.messageEmbed)
                try:
                    await lobby.originalMessage.delete()
                except Exception:
                    print(lobby.hostName + "'s lobby message already deleted")
                await tempPointer.add_reaction(self.thumbsUP)
                lobby.originalMessage = tempPointer
            
            # Update openlobbies embed list
            if self.lobbyMessage != None:
                await self.updateOpenLobbies()
            return

        steamID = self.accountLinks.get(str(hostID), None)
        if steamID == None:
            await message.channel.send("Your account is not linked!")
            return

        profileResponse = requests.get(self.profileLookUp + str(steamID))
        if profileResponse.status_code != 200:
            # error
            await message.channel.send("Error Code")
            return

        # parse for game join link
        lobbyLink = re.search("steam://joinlobby(.*)\" ",profileResponse.text)
        if lobbyLink != None:
            lobbyLink = lobbyLink.group(0).rstrip("\" ")
            lobbyLink = lobbyLink.rstrip("\"")
        else:
            await message.channel.send("Error retreiving link. Ensure that your account is not private and you are in a joinable lobby!")
            return

        appID = re.split("[/]+", lobbyLink)[2]
        lobbyID = re.split("[/]+", lobbyLink)[3]

        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                await message.channel.send("Error id")
                return
        
        embeddedMessage = self.generateEmbedMessage(appID, host, lobbyLink)    
        self.lobbies[hostID] = steamLobby(str(hostID),host.display_name,appID,self.gamesList[appID]["Name"], None, embeddedMessage, steamID, lobbyID, self)
        
        
        # Parse for arguments to !host call
        lobbyArgs = {"image" : 1, "note" : 2}
        splitMessage = message.content.split(",")
        for index in range(0,len(splitMessage),1):
            splitString = splitMessage[index].split(":=")
            result = lobbyArgs.get(splitString[0].lstrip(),-1)
            if result != -1:
                if result == 1:
                    # parse image content
                    message.content = splitString[1]
                    await self.addImage(message,False)
                elif result == 2:
                    # parse footer content
                    message.content = splitString[1]
                    await self.addNote(message,False)


        if self.lobbies[hostID].imageFile == None:
            self.lobbies[hostID].originalMessage = await message.channel.send(embed=embeddedMessage)
        else:
            self.lobbies[hostID].originalMessage = await message.channel.send(file=self.lobbies[hostID].imageFile, embed=embeddedMessage)
        
        # Update openlobbies embed list
        if self.lobbyMessage != None:
           await self.updateOpenLobbies()
        
        await self.lobbies[hostID].updatePlayers()
        

    async def embedLobby(self, message): # DONE
        # Dont track users in this lobby but make an embedded message for the lobby
        # STEAM://JOINLOBBY/<APPID>/<STEAMLOBBYID>/steamID>

        host = message.author
        splitMessage = re.split("[/]+", message.content)

        if splitMessage[0] != "steam:" and splitMessage[1] != "joinlobby":
            # most likely an invalid lobby
            await message.channel.send("Could not retreive steam lobby")
            return
        
        appID = splitMessage[2]
        
        # check if games data is already stored
        if self.gamesList.get(appID,None) == None:
            if not self.addGame(appID):
                print("Unable to add game data to SOPBot")
                return

        embeddedMessage = self.generateEmbedMessage(appID, host, message.content)
        await message.channel.send(embed=embeddedMessage)

    def generateEmbedMessage(self, appID, host, lobbyLink): #DONE exception of updates
        game = self.gamesList[appID]
        # VERSION 1
        # embeddedMessage = discord.Embed(title = game["Name"] + " lobby")
        # embeddedMessage.set_thumbnail(url=str(game["Images"][0]))
        # embeddedMessage.set_author(name= host.name + "'s", icon_url=host.avatar_url)
        # embeddedMessage.add_field(name="Link: ", value=lobbyLink, inline=True)
        
        # VERSION 2
        embeddedMessage = discord.Embed(title=lobbyLink)
        embeddedMessage.set_thumbnail(url=str(game["Images"][0]))
        embeddedMessage.set_author(name=host.display_name + "'s " + game["Name"] + " lobby", icon_url=host.avatar_url)
        return embeddedMessage


    def addGame(self,appID): #DONE

        # game is not in list, retreive data from steam
        response = requests.get(self.steamURL  + appID + "/")
        if response.status_code != 200:
            # error retreiving game
            return False
        
        # parse data from response
        nameResult = re.search("apphub_AppName\">(.+)<", response.text)
        # use default steam icon
        iconResult = "https://cdn.akamai.steamstatic.com/steam/apps/"
        iconResult += appID 
        iconResult += "/header.jpg"

        # will need improvement
        nameResult = nameResult.group(0).split(">")[1].rstrip("<")

        # add basic information to steam gamesList
        self.gamesList[appID] = {}
        self.gamesList[appID]["Name"] = nameResult
        self.gamesList[appID]["Images"] = []
        self.gamesList[appID]["Images"].append(iconResult)

        # store game image inside respective folder, if game folder doesnt exist, then create it
        gameDirectory = "../Game_Files/" + nameResult + "/"
        if os.path.isdir(gameDirectory) == False: # directory doesnt exist 
            print("Creating directory for " + nameResult)
            os.mkdir(gameDirectory)

        gameIcon = requests.get(iconResult)
        if gameIcon.status_code == 200:
            gameImage = open(gameDirectory + "gameIcon.jpg", "wb")
            gameImage.write(gameIcon.content)
        return True

    async def linkAccount(self, message):
        # Retreive users steam account information and save
        try:
            content = message.content.split("/")
            steamURL = content[4]
        except IndexError:
            await message.channel.send("Error parsing steam URL. Ensure link is valid.")
            return

        url_response = requests.get(self.lookUpUrl + steamURL)
        if url_response.status_code != 200:
            # if we dont get a valid response
            await message.channel.send("Error linking account!")
            return

        match = re.search("data-steamid64=\"\d+", url_response.text).group(0)
        steamID64 = match.split("\"")[1]
        authorID = str(message.author.id)

        # verify that the account hasnt been used yet
        for discordUser in self.accountLinks:
            if authorID == discordUser:
                await message.channel.send("Your Discord account is already linked to a steam account.")
                return
            elif steamID64 == self.accountLinks[discordUser]:
                discordUser = await self.client.fetch_user(int(authorID))
                await message.channel.send("Provided Steam account is already linked to " + discordUser.display_name)
                return

        # add steamID64 to json of users linked to the lobby system
        self.accountLinks[authorID] = steamID64 
        await message.channel.send("Successful link!")

    async def displayOpenLobbies(self,message):
        lobbyEmbed = discord.Embed(title = "Open Lobbies")
        fileName = "junyaTHUMB.jpg"
        imageFile = discord.File(fileName, filename=fileName)
        lobbyEmbed.set_thumbnail(url="attachment://" + fileName)

        # display count of lobbies open
        count = len(self.lobbies)
        if count == 0:
            lobbyEmbed.set_footer(text="Currently no lobbies are open.")
        elif count == 1:
            lobbyEmbed.set_footer(text="Currently 1 lobby is open.")
        else:
            lobbyEmbed.set_footer(text="Currently " + str(count) + " lobbies are open.")

        for lobby in self.lobbies:
            thisLobby = self.lobbies[lobby]
            gameName = "***" + thisLobby.gameName + "***  "
            hostName = "Host: " + thisLobby.hostName + " Player Count: " + str(self.lobbies[lobby].playerCount)
            hostName += "  [Lobby](" + thisLobby.originalMessage.jump_url + ")"
            lobbyEmbed.add_field(name=gameName, value=hostName,inline=False)

        if self.lobbyMessage != None:
            try:
                await self.lobbyMessage.delete()
            except:
                print("Attempted to delete open lobbies message that was already deleted!")
        
        self.lobbyMessage = await message.channel.send(file=imageFile,embed=lobbyEmbed)

    async def updateOpenLobbies(self):
        lobbyEmbed = discord.Embed(title = "Open Lobbies")
        fileName = "junyaTHUMB.jpg"
        imageFile = discord.File(fileName, filename=fileName)
        lobbyEmbed.set_thumbnail(url="attachment://" + fileName)

        print("update called")
        # display count of lobbies open
        count = len(self.lobbies)
        if count == 0:
            lobbyEmbed.set_footer(text="Currently no lobbies are open.")
        elif count == 1:
            lobbyEmbed.set_footer(text="Currently 1 lobby is open.")
        else:
            lobbyEmbed.set_footer(text="Currently " + str(count) + " lobbies are open.")

        for lobby in self.lobbies:
            thisLobby = self.lobbies[lobby]
            gameName = "***" + thisLobby.gameName + "***  "
            hostName = "Host: " + thisLobby.hostName + " Player Count: " + str(self.lobbies[lobby].playerCount)
            hostName += "  [Lobby](" + thisLobby.originalMessage.jump_url + ")"
            lobbyEmbed.add_field(name=gameName, value=hostName,inline=False)
        
        if self.lobbyMessage != None:
            await self.lobbyMessage.edit(embed=lobbyEmbed)
            # try:
            #     
            # except Exception:
            #     # lobby message most likely deleted
            #     await self.lobbyMessage.channel.send(file=imageFile,embed=lobbyEmbed)


    async def closeLobby(self, message):
        # delete lobby from list
        
        authorID = str(message.author.id)
        lobby = self.lobbies.get(authorID, None)
        if lobby == None:
            await message.channel.send("No hosted lobby being tracked by SOPBot!")
            return

        await lobby.closeLobby()
        self.lobbies.pop(authorID)

        if self.lobbyMessage != None:
            await self.updateOpenLobbies()

    async def addNote(self, message, post=True):
        # add a footer to the lobby 

        authorID = str(message.author.id)
        lobby = self.lobbies.get(authorID, None)
        if lobby == None:
            await message.channel.send("No hosted lobby being tracked by SOPBot!")
            return

        lobby.messageEmbed.set_footer(text=message.content)
        if post:
            await lobby.originalMessage.edit(embed=lobby.messageEmbed)

    async def addImage(self,message, post=True):
        authorID = str(message.author.id)
        lobby = self.lobbies.get(authorID, None)
        if lobby == None and post:
            await message.channel.send("No hosted lobby being tracked by SOPBot!")
            return

        requestOutput = None
        try:
            requestOutput = requests.get(message.content)
        except Exception:
            print("Invalid image URL.")
        
        if requestOutput != None and requestOutput.status_code == 200:
            lobby.imageName = message.content
            lobby.imagePath = None
            lobby.messageEmbed.set_image(url=message.content)

            if post:
                tempPointer = await lobby.originalMessage.channel.send(embed=lobby.messageEmbed)
                await lobby.originalMessage.delete()
                await tempPointer.add_reaction(self.thumbsUP)
                lobby.originalMessage = tempPointer
                await message.delete()
                await self.updateOpenLobbies()
            return
        
        elif len(message.attachments) > 0:
            # see if an attachment was made for this message
            print("do noting for now since Idk what to do yet haha.")
        
        # default
        lobby.imagePath, lobby.imageName = self.client.handlers["~"].retrieveFilePath(message.content) 
        if lobby.imageName == None and post:
            await message.channel.send("Not a valid image!")
            return
        
        imageFile = discord.File(lobby.imagePath, filename=lobby.imageName)
        lobby.messageEmbed.set_image(url="attachment://" + lobby.imageName)
        lobby.imageFile = imageFile
        
        if post:
            tempPointer = await lobby.originalMessage.channel.send(file=imageFile,embed=lobby.messageEmbed)
            # reset message with reactions 
            #await lobby.originalMessage.clear_reactions()
            await lobby.originalMessage.delete()
            await tempPointer.add_reaction(self.thumbsUP)
            lobby.originalMessage = tempPointer
            
            await self.updateOpenLobbies()

class steamLobby():
    # Handle updating players and retreiving if lobby is still open
    REQUEST_KEY = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&"
    TEST_STRING = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=5355C4BC38BDD5BE29B4CE3DA2495936&format=json&steamids=76561198240844888,76561198051944687"
    
    def __init__(self, hostID, hostName, appID, gameName, messageID, embeddedMessage, steamID, lobbyID, lobbyHandler):
        self.hostID = hostID
        self.hostName = hostName
        self.appID = None
        self.gameName = gameName
        self.players = {}
        self.originalMessage = messageID
        self.lobbyID = lobbyID
        self.playerCount = 1
        self.messageEmbed = embeddedMessage
        # add the host as the first person in the message
        self.messageEmbed.add_field(name="Player#" + str(self.playerCount), value=self.hostName)
        self.terminateFlag = False
        self.players[steamID] = [0, self.hostName] # format lobby position, name
        self.lobbyHandler = lobbyHandler
        self.thumbsUP = "👍"
        self.imagePath = None
        self.imageName = None
        self.imageFile = None

    def cleanUp():
        self.terminateFlag = True
    
    def getMessageID(self):
        return self.originalMessage.id
    
    def addPlayer(self, steamID, name):
        # add this player to the track list for this steam lobby
        self.players[steamID] = [-1, name] # set to -1 for index
        return True

    async def updatePlayers(self):
        # check status of players and ensure that they're in the lobby
        # https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=<keyhere>&steamids=<csv steamid64 keys>
        # 5355C4BC38BDD5BE29B4CE3DA2495936
        
        await self.originalMessage.edit(embed=self.messageEmbed)
        await self.originalMessage.add_reaction(self.thumbsUP)

        while(self.playerCount > 0):              

            requestPackage = steamLobby.REQUEST_KEY + "steamids=" + str(self.players)
            response = requests.get(requestPackage)
            response = response.json()
        
            playerList = response['response']['players']
            
            print("Players Count: " + str(self.playerCount))
            print("Players watching " + str(len(self.players)))

            for player in playerList:
                steamid = player['steamid']
                lobbyID = str(player.get('lobbysteamid',-1)) # set to -1 if not in a lobby
                
                if lobbyID != self.lobbyID and self.players[steamid][0] != -1:
                    # user is not in the lobbylobbyID
                    #if steamid in self.players:

                    if self.lobbyHandler.accountLinks[self.hostID] == steamid:
                        # host left the lobby, destroy. (Assume that lobbies close when host leaves)
                        print("Host has left the lobby, closing lobby!")
                        await self.closeLobby(True)
                        return

                    if self.playerCount > 1:
                        # remove this player and shift other players down one position
                        playerIndex = int(self.players[steamid][0])
                        self.messageEmbed.remove_field(playerIndex) # remove field will auto shift indexes, but name/values will remain same
                        for fieldIndex in range(len(self.messageEmbed.fields)):
                            origValue = self.messageEmbed.fields[fieldIndex].value
                            self.messageEmbed.set_field_at(fieldIndex,name= "Player#" + str(fieldIndex + 1), value=origValue)
                        await self.originalMessage.edit(embed=self.messageEmbed)

                        for index in self.players:
                            # adjust player positions in dictionary
                            selectedPlayerIndex = int(self.players[index][0])
                            if selectedPlayerIndex > playerIndex:
                                self.players[index][0] = selectedPlayerIndex - 1

                        self.players[steamid][0] = -1
                        self.playerCount -= 1
                    else:
                        print("Closing " + self.hostName + "'s lobby.")
                        self.playerCount = 0
                        # await self.closeLobby()
                        # lobby = self.lobbyHandler.lobbies.pop(self.hostID)
                        # del lobby
                        await self.closeLobby(True)
                        return

                else:
                    # user is in the lobby
                    if lobbyID == self.lobbyID and self.players[steamid][0] == -1:
                        print("updating player position")
                        # add them to the list, otherwise ignore
                        self.players[steamid][0] = self.playerCount # set their index and their name
                        self.messageEmbed.add_field(name="Player#" + str(self.playerCount + 1), value = self.players[steamid][1])
                        await self.originalMessage.edit(embed=self.messageEmbed)
                        self.playerCount += 1

            await asyncio.sleep(15) # wait 15 seconds before updating again
            if self.terminateFlag:
                # use busy wait terminate on close for now
                return

    async def closeLobby(self, selfClose=False):
        self.playerCount = 0
        self.messageEmbed.clear_fields() # remove all players from the lobby
        self.messageEmbed.add_field(name="Lobby Status:", value="Closed", inline=True)
        await self.originalMessage.edit(embed=self.messageEmbed)

        if selfClose:
            # Bot automatically closed instead of using !close
            self.lobbyHandler.lobbies.pop(self.hostID)
            await self.lobbyHandler.updateOpenLobbies()
            

    def selectNewHost(self):
         # if the host leaves the lobby and lobby remains open(I think some games allow this)
        pass  