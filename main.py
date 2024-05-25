DISCORD_TOKEN = "placeHolder"

import discord

client = discord.Client(intents=discord.Intents(messages=True, message_content=True))

from coreClassesAndFunctions import variableProcessPointer,home,userSet,handleOutput,timers

# apps
from chameleon import chameleonMenu

timersProcess = timers()

subProcesses = [timersProcess]

def shutUp(info):

    # turns off all subprocesses
    for subProcess in subProcesses:
        subProcess.stop()
    subProcesses.clear()

    @client.event
    async def on_message(message):

        if message.content == "!setup":
            currentChannel = message.channel

            # list of users I'm expecting DMs from
            expectingDMsFrom = userSet()
            # I keep track of the current process using a pointer.
            currentProcess = variableProcessPointer()
            # The initial process (home) is given a pointer to allow it to change the current process in the future.
            currentProcess.set(home(currentProcess.set,{"chameleon":chameleonMenu}))

            # setting constant info
            info = {"currentProcess":currentProcess,"mainChannel":currentChannel,"expectingDMsFrom":expectingDMsFrom,"changeProcess":currentProcess.set,"timer":timersProcess}

            await currentChannel.send("I (the Mobot) have been successfully setup. I am a discord CLI for python applications. Try !commands to see what I can do.")

            @client.event
            async def on_message(message):

                isCommand = message.content.startswith('!')
                isNotMe = not message.author == client.user
                isDM = isinstance(message.channel,discord.DMChannel) and expectingDMsFrom.checkUser(message.author)
                isExpectedChannel = message.channel == currentChannel or isDM

                if isCommand and isNotMe and isExpectedChannel:

                    input = message.content[1:]

                    split = input.split(" ", 1)
                    command = split[0]

                    try:
                        parameter = split[1]
                    except IndexError:
                        parameter = ""

                    # adding on variable info
                    try:
                        info.update({"parameter":parameter,"sender":message.author,"isDM":isDM,"currentChannel":message.channel})
                    except AttributeError:
                        pass

                    try:
                        output = currentProcess.get().getCommands()[command](info)
                    except KeyError:
                        try:
                            output = permanentCommands[command](info)
                        except KeyError:
                            output = f"I'm afraid that the command !{command} doesn't exist, try running !commands for a list of valid commands"

                    await handleOutput(output,message.channel)

def displayCurrentCommands(info):
    currentProcess = info["currentProcess"]

    commandList = ""
    for command in currentProcess.get().getCommands().keys():
        commandList += "!"+command+"\n"
    for command in permanentCommands.keys():
        commandList += "!" + command + "\n"

    return commandList

permanentCommands = {"commands":displayCurrentCommands,"shutUp":shutUp}

@client.event
async def on_ready():
    shutUp("") # puts the bot into its off state

client.run(DISCORD_TOKEN)
