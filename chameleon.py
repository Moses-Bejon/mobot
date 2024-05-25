import random

from coreClassesAndFunctions import process
from lobby import lobby

class chameleonMenu(process):
    def __init__(self,parentProcess,changeProcess):
        super().__init__(parentProcess,changeProcess)
        self._addCommands({
            "play": self.play,
            "addDeck": self.addDeck,
            "deleteDeck": self.deleteDeck,
            "viewDecks": self.viewDecks,
            "rules": self.rules
        })

    def play(self,info):
        self._changeProcess(lobby(self,self._changeProcess,chameleonGame,3))
        return "Sending you to the chameleon lobby, try !join to join the game and !begin to start"

    def rules(self,info):
        return """All players get thirty seconds to think of a suitably obscure hint and DM it to me while the chameleon waits.
After the thirty seconds a random player is chosen to be the leader. Their hint is revealed to chameleon.
The chameleon gets thirty seconds to examine the leader's hint and think of a good hint to blend in with while the players wait.
After this the leader is revealed to all the players (so the players know the chameleon copied the leader's hint).
All participants (leader and chameleon included) then have thirty seconds to vote on who they think the chameleon is.
If a player other than the chameleon gets the most votes, the chameleon wins.
If the chameleon gets the most votes, the chameleon gets 30 seconds to guess what they think the card was.
If the chameleon guesses correctly, they win, otherwise, they lose.

Revision rules:
If we are playing with a deck for revision purposes, hints must require some technical aspect of the card's academic meaning to understand.
i.e:
Polymorphism
We've had this one in a previous round❌
Made up of two root words and a suffix❌
Sounds like a pokemon without the end❌
The first letter is P❌
One bit of code works for so many different types of things✔
I have no idea who you are✔
They're all the same to me✔

Timings can be adjusted if needed.
"""

    def addDeck(self,info):
        deck = info["parameter"]

        if deck == "":
            return """you need to put the name of the deck after the command (a space between the two) and then all the cards you want with spaces between the different cards.
            for example:
            !addDeck numbers 1 2 3 4 5
            or
            !addDeck nerds Moses_Bejon Shubhangee_Das Andrew_Zhang Hera_Choi Judd_Bayona
            (would be embarrassing if I spelt someone's name wrong)"""

        words = deck.split(" ")

        if len(words) == 1:
            return "every deck must have at least one card"

        with open("chameleonDecks.txt", "a") as decks:
            decks.write("\n" + deck)

        output = "I have created a deck called " + words[0] + ", this deck contains the following cards:\n"
        for word in words[1:]:
            output += word + "\n"
        output += "if this wasn't what you expected please delete the deck using !deleteDeck"

        return output

    def deleteDeck(self,info):
        deckName = info["parameter"]

        with open("chameleonDecks.txt", "r") as file:
            decks = file.readlines()

        if len(decks) == 1:
            return "I can't delete the last deck, there must always be at least one deck in the file"

        position = 0
        for deck in decks:

            if deck.split(" ", 1)[0] == deckName:
                decks = decks[:position] + decks[position + 1:]
                break
            position += 1

        else:
            return "could not find a deck called: " + deckName

        with open("chameleonDecks.txt", "w") as file:
            file.writelines(decks)

        return "deleted " + deckName

    def viewDecks(self,info):
        with open("chameleonDecks.txt", "r") as file:
            return file.read()

class chameleonGame(process):
    def __init__(self,parentProcess,changeProcess,players):
        super().__init__(parentProcess,changeProcess)
        self._addCommands({
            "pickDeck":self.pickDeck
        })
        self.__players = players


    def pickDeck(self,info):

        info["expectingDMsFrom"].setUsers(self.__players)

        self._removeCommands(("viewDecks", "pickDeck"))
        self.__deck = info["parameter"]
        self._addCommands({"hint": self.giveHint,"viewCards":self.viewCards})

        with open("chameleonDecks.txt","r") as file:
            file = file.readlines()

        for line in file:
            if line.split(" ",1)[0] == self.__deck:
                self.__deck = line.split(" ")[1:]
                break
        else:
            return f"the deck {self.__deck} does not exist, try !viewDecks to find one that does"

        self.__cardChosen = random.choice(self.__deck)
        self.__chameleon = random.choice(list(self.__players.getUsers()))

        self.__nonChameleonPlayers = self.__players.getUsers().copy()
        self.__nonChameleonPlayers.remove(self.__chameleon)

        self.__hints = {}

        output = {}
        for player in self.__nonChameleonPlayers:
            output[player] = f"You're a player. The card chosen is {self.__cardChosen}. DM me your hint using !hint on this channel within 30 seconds."
        output[self.__chameleon] = "You're the chameleon, I'll DM you after 30 seconds with the leader's hint"

        info["timer"].createTimer(30,self.getChameleonHint,info)

        return output

    def viewCards(self,info):
        output = ""
        for card in self.__deck:
            output += card+"\n"
        return output

    def getChameleonHint(self,info):
        self._removeCommands(("hint",))

        for player in self.__players.getUsers():
            if player not in self.__hints:
                self.__hints[player] = "This participant failed to provide me with a hint"

        self._removeCommands(("giveHint",))
        self._addCommands({"guessHint": self.guessHint})
        self.__leader = random.choice(list(self.__nonChameleonPlayers))

        info["timer"].createTimer(30,self.beginVoting,info)
        return {self.__chameleon:f"The leader's hint was {self.__hints[self.__leader]}. You  have thirty seconds to think of a hint, use !guessHint to submit your hint."}

    def close(self,info):
        info["expectingDMsFrom"].clear()
        super().close(info)

    def beginVoting(self,info):

        self._removeCommands(("guessHint",))
        self.__votes = {}
        self.__tally = [0] * (len(self.__hints)-1)
        self._addCommands({"vote":self.vote})

        output = f"The leader was {self.__leader}, and their hint was {self.__hints[self.__leader]}. The other hints were:"

        # the leader's hint is not an option for voters
        del self.__hints[self.__leader]
        self.__hints = list(self.__hints.items())

        # remove any information the order of the listed dictionary may contain
        random.shuffle(self.__hints)

        for i,(hinter,hint) in enumerate(self.__hints):
            # the invisible character is there to prevent discord from marking up my 0 to a 1
            # (which it does for some reason and the normal \ to remove formatting doesn't correct it)
            output += f"\n‎{i}. {hinter}:{hint}"


        output += "\nUse !vote and then the number you want to vote for, i.e !vote 3"

        info["timer"].createTimer(30,self.tallyVotes,info)

        return {info["mainChannel"]:output}

    def tallyVotes(self,info):

        maximumIndices = []
        maximum = -1

        for i,number in enumerate(self.__tally):
            if number > maximum:
                maximumIndices = [i]
                maximum = number
            elif number == maximum:
                maximumIndices.append(i)

        if len(maximumIndices) == 1:
            if self.__hints[maximumIndices[0]][0] == self.__chameleon:
                self._removeCommands(["vote","viewCards"])

                self.__chameleonGuessTimer = info["timer"].createTimer(30, self.endGame, info)

                self._addCommands({"guess":self.guess})

                return {info["mainChannel"]:f"The chameleon, {self.__chameleon}, was correctly voted for. They now have thirty seconds to guess what the card was.\ni.e. !guess {random.choice(self.__deck)}"}

            self._removeCommands(["vote","viewCards"])
            self._addCommands({"pickDeck":self.pickDeck})
            return f"You voted for {self.__hints[maximumIndices[0]][0]} and the chameleon was {self.__chameleon}. Players lose."

        hints = []
        for maximumIndex in maximumIndices:
            hints.append(self.__hints[maximumIndex])
        self.__hints = hints
        self.__votes = {}
        self.__tally = [0]*len(self.__hints)
        output = "There was a tie. We will be redoing the vote with the tied participants:"

        # remove any information the order may contain
        random.shuffle(self.__hints)

        for i, (hinter, hint) in enumerate(self.__hints):
            output += f"\n‎{i}. {hinter}:{hint}"

        info["timer"].createTimer(30, self.tallyVotes, info)

        return output



    def endGame(self,info):
        self._removeCommands(["guess"])
        self._addCommands({"pickDeck": self.pickDeck})
        return "The chameleon failed to submit a guess within thirty seconds. Players win"

    def guess(self,info):
        sender = info["sender"]
        if sender != self.__chameleon:
            return f"You ({sender}) are not the chameleon, therefore, you cannot guess what you think the card is"

        info["timer"].removeTimer(self.__chameleonGuessTimer)

        guess = info["parameter"]

        self._removeCommands(["guess"])
        self._addCommands({"pickDeck": self.pickDeck})



        if guess == self.__cardChosen:
            return f"The chameleon has guessed the correct card and won the game"

        return f"The chameleon has guessed the wrong card ({guess}). The correct card was {self.__cardChosen}. Players win"


    def vote(self,info):
        voter = info["sender"]
        vote = info["parameter"]

        try:
            vote = int(vote)
        except:
            return f"Could not recognise your ({voter}'s) vote, '{vote}', as an integer"

        if vote < 0 or vote >= len(self.__hints):
            return f"{voter}'s vote, '{vote}', is not on the list of possible votes"

        if voter in self.__votes:
            self.__tally[self.__votes[voter]] -= 1

        self.__votes.update({voter:vote})
        self.__tally[vote] += 1

        return f"{voter}'s vote for {vote} ({self.__hints[vote][0]}) has been received"

    def giveHint(self,info):
        hinter = info['sender']

        if hinter == self.__chameleon:
            return {hinter:f"You can't give your hint yet, wait until the 30 seconds are up"}

        hint = info["parameter"]

        if info["isDM"] == False:
            self._removeCommands(["hint"])
            self._addCommands({})
            return f"Unfortunately this round has to be declared null and void as a user has submitted their hint to the public channel. {hinter}, please DM me your hint next time."

        self.__hints[hinter] = hint
        return {hinter:f"your hint, {hint}, has been stored. You can still submit another hint as long as it's before the time limit"}

    def guessHint(self,info):
        hinter = info["sender"]
        hint = info["parameter"]

        if hinter != self.__chameleon:
            return {hinter:f"Sorry, the thirty seconds are up"}

        self.__hints.update({hinter:hint})
        return {hinter:f"Your hint, {hint}, has been stored. You can still submit another hint as long as it's before the time limit"}






