from asyncio import create_task,sleep,CancelledError

class process():
    def __init__(self,parentProcess,changeProcess):
        self.__parentProcess = parentProcess
        self._commands = {"close":self.close}
        self._changeProcess = changeProcess

    def getCommands(self):
        return self._commands

    def close(self,info):
        self._changeProcess(self.__parentProcess)
        return "Closed current process"

    def _removeCommands(self,commands):
        for command in commands:
            try:
                del self._commands[command]
            except KeyError:
                pass

    def _addCommands(self,commands):
        self._commands.update(commands)

# this hideous bit of code exists because I want to be able to have processes change where this pointer leads without
# using global variables and I also wanted it to be empty if necessary before it is instantiated
class variableProcessPointer():
    def __init__(self):
        pass
    def set(self,process):
        self.__process = process
    def get(self):
        return self.__process

class userSet():
    def __init__(self):
        self.__users = set()

    def addUser(self,user):
        self.__users.add(user)

    def removeUser(self,user):
        self.__users.remove(user)

    def clear(self):
        self.__users = set()

    def setUsers(self,userSet):
        self.__users = userSet.getUsers().copy()

    def checkUser(self,user):
        return user in self.__users

    def getUsers(self):
        return self.__users

    def length(self):
        return len(self.__users)

class home(process):
    def __init__(self,changeProcess,apps):
        super().__init__(None,changeProcess)

        for applicationName,applicationClass in apps.items():
            self._commands[applicationName] = self.__createApplicationRunFunction(applicationName,applicationClass,changeProcess)


    def close(self,info):
        return "You can't close home, if you want me to shut up say so (!shutUp)"

    def __createApplicationRunFunction(self,applicationName,applicationClass,changeProcess):
        def runApplication(info):
            self._changeProcess(applicationClass(self,changeProcess))
            return f"opened {applicationName} application"
        return runApplication

async def handleOutput(output, currentChannel):
    if isinstance(output, str):
        await currentChannel.send(output)
    elif isinstance(output, dict):
        for user, message in output.items():
            await user.send(message)

class timers:
    def __init__(self):
        self.__timers = set()

    def createTimer(self,delay, callback, info, silent=False):

        # ensures the info that was passed into timer remains as its info
        # otherwise, if info changes elsewhere in the program, that will affect the timer
        info = info.copy()

        if silent:
            timer = create_task(self.__silentTimer(delay, callback, info))
        else:
            timer = create_task(self.__loudTimer(delay, callback, info))

        self.__timers.add(timer)

        return timer

    def removeTimer(self,timer):
        self.__timers.remove(timer)
        timer.cancel()

    def stop(self):
        for timer in self.__timers:
            timer.cancel()
        self.__timers = set()


    async def __loudTimer(self,delay, callback,info):
        try:
            channel = info["mainChannel"]
            await channel.send(f"A {delay} second timer has begun")

            if delay > 10:
                await sleep(delay - 10)
                await channel.send("10 seconds left")
                await sleep(10)
            else:
                await sleep(delay)

            await channel.send("time's up")

            await handleOutput(callback(info), channel)
        except CancelledError:
            pass


    async def __silentTimer(self,delay, callback,info):
        try:
            await sleep(delay)
            await handleOutput(callback(info), info["mainChannel"])
        except CancelledError:
            pass