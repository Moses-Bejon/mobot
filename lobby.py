from coreClassesAndFunctions import process, userSet

class lobby(process):
    def __init__(self,parentProcess,changeProcess,game,minPlayers=1,maxPlayers=100):
        super().__init__(parentProcess,changeProcess)

        self._addCommands({
            "join":self.join,
            "leave":self.leave,
            "begin":self.begin
        })

        self.__minPlayers = minPlayers
        self.__maxPlayers = maxPlayers
        self.__game = game
        self.__players = userSet()


    def join(self,info):
        sender = info["sender"]

        if self.__players.checkUser(sender):
            return f"you ({sender}) have already joined the game"

        self.__players.addUser(sender)

        return f"{sender} has joined"

    def leave(self,info):
        sender = info["sender"]

        if not self.__players.checkUser(sender):
            return f"you ({sender}) didn't join the game"

        self.__players.removeUser(sender)

        return f"{sender} has left"

    def begin(self,info):
        if self.__players.length() < self.__minPlayers:
            return f"cannot begin game as there are not enough players (number of players:{self.__players.length()},number of players required:{self.__minPlayers})"
        if self.__players.length() > self.__maxPlayers:
            return f"cannot begin game as there are too many players (number of players:{self.__players.length()},maximum number of players:{self.__maxPlayers})"

        self._changeProcess(self.__game(self,self._changeProcess,self.__players))

        return "game has began"

