import random

#GameState holds all the relevant information and functions related to the table as well as game rules that the user can adjust.
class GameState:
    shoe = []
    shoe_value = 0
    players_list = []

    #These four values determine the maximum possible value of cards on the table, used to calculate the minimum end-of-round shoe value before adding decks.
    max_dealer_hand = 26
    max_player_hand = 30
    max_players = 5
    max_hands = 2

    decks = 1 #By default, the game is single-deck Blackjack.
    deck_value = 0 #Ace value is counted as 1 for the purpose of shoe management.
    buy_in = 1000.00 #Also used for rebuys.
    casino_name = "Moonshadow Casino"
    surrender_allowed = True #By default, players can surrender half their bet on the first turn. Most casinos no longer allow this.

    def __init__(self):
        self.deck_list = self.create_deck()
        self.dealer = Player("Dealer", self)

    #While it would be possible to manually fill out a deck or pull from a file, this simplifies the process. This process also allows for users to create custom decks.
    def create_deck(self):
        base_deck = []
        deck_list = []
        suits = ["♠", "♥", "♣", "♦"]
        ranks = ["A"]
        single_deck_value = 0
        for n in range(2, 11):
            ranks.append(str(n))
        ranks.extend(["J", "Q", "K"])
        for s in suits:
            for r in ranks:
                base_deck.append(Card(r, s))
                single_deck_value += self.get_card_value(r) #340 with a standard deck.
        for d in range(self.decks):
            deck_list.extend(base_deck) #Provides a total deck list to be shuffled together every time the shoe runs low.
        self.deck_value = self.decks * single_deck_value #Value of all cards in deck_list
        return deck_list

    #Returns the minimum value of cards in order to be added to the base deck value.
    def get_card_value(self, rank):
        if rank in "JQK":
            return 10
        elif rank == "A":
            return 1
        return int(rank)

    #Displays a welcome message for the players when they enter the casino.
    def display_welcome(self):
        welcome_message = "\033[96mWelcome to {casino}! Decks shuffled into the shoe: {decks}. Max players per table: {players}. Max number of hands per player: {hands}. Surrenders are \033[0m".format(casino = self.casino_name, decks = self.decks, players = self.max_players, hands = self.max_hands)
        if self.surrender_allowed:
            welcome_message += "\033[96mallowed.\033[0m"
        else:
            welcome_message += "\033[96mnot allowed.\033[0m"
        print(welcome_message)

    #Creates an instance of the Player class for each player participating in the game and adds them to the list of players. Defaults the name to "Player X" (X being the player number) if the player does not enter a name.
    def create_players(self):
        num_players = self.get_num_players()
        for p in range(num_players):
            pname = input("What is the name for player {num}? ".format(num = p + 1))
            if not pname:
                self.players_list.append(Player("Player {num}".format(num = p + 1), self))
            else:
                self.players_list.append(Player(pname, self))

    #Gets the number of players that will be playing and verifies that the user inputs an actual number between 1 and max_players.
    def get_num_players(self):
        while True:
            try:
                pinput = int(input("Choose the number of players (1-{max}): ".format(max = self.max_players)))
                if 1 <= pinput <= self.max_players:
                    num_players = pinput
                    return num_players
                elif pinput > self.max_players:
                    print("The table can't hold that many players!")
                else:
                    print("At least one person needs to be playing for a game to happen.")
            except ValueError:
                print("That's not a number.")

    #Checks to see if the shoe has enough cards for a full round. If not, it calls add_to_shoe to add a deck (or set of decks) to the shoe with a message that changes depending on whether or not the shoe is empty when the dealer extends the shoe.
    def check_shoe_size(self):
        min_value = self.get_min_shoe()
        while self.shoe_value < min_value:
            if self.shoe_value > 0:
                print("The dealer adds another deck to the shoe.")
            else:
                print("The dealer adds a deck to the shoe")
            self.shoe_value += self.add_to_shoe() #Updates the total value of cards currently in the shoe.

    #Calculates the minimum value of cards needed for a full round based on the maximum number of hands and theoretical maximum value of those hands.
    def get_min_shoe(self):
        return self.max_dealer_hand + (len(self.players_list) * self.max_hands * self.max_player_hand)

    #Adds a newly shuffled deck(s) to the shoe, moving the old deck(s) to the end of the list to ensure that every card from the deck(s) is dealt before the first card of the new deck(s) is dealt.
    def add_to_shoe(self):
        old_deck = self.shoe
        new_deck = self.deck_list.copy()
        random.shuffle(new_deck)
        self.shoe = new_deck + old_deck
        return self.deck_value

    #Creates a hand for each player, takes their bets, and deals the initial set of cards. Also provides the board state at the start of the round.
    def initial_deal(self):
        self.starter_hands()
        players_to_remove = self.handle_betting()
        self.remove_player(players_to_remove)
        if len(self.players_list) > 0: #Skips dealing if all players leave the game.
            for d in range(2):
                for p in self.players_list:
                    self.deal_cards(p.hands[0])
                self.deal_cards(self.dealer.hands[0])
            for p in self.players_list:
                p.hands[0].print_hand()
                p.hands[0].check_blackjack()
            self.dealer.show_upcard()
            self.dealer.hands[0].check_blackjack()
            print("-------------------------------------------------") #Provides a break between showing the initial board state to the players and the individual players' actions in order to avoid confusion.

    #Handles player betting inputs for their initial hands as well as giving them the option to leave.
    def handle_betting(self):
        players_to_remove = []
        for p in self.players_list:
            while p.hands[0].bet == 0:
                binput = input("{player} has ${money} remaining. How much will {player} bet? Enter 0 or \"leave\" to leave. ".format(player = p.name, money = p.bankroll))
                p.hands[0].bet = p.betting(binput)
            if p.hands[0].bet == -1:
                players_to_remove.append(p)
            else:
                p.bankroll -= p.hands[0].bet
        return players_to_remove

    def remove_player(self, players_to_remove):
        for r in players_to_remove:
            self.players_list.remove(r)

    def starter_hands(self):
        for p in self.players_list:
            p.hands.append(Hand(1, p))
        self.dealer.hands.append(Hand(1, self.dealer))

    #Deals a card to the player's hand, removing it from the shoe and updating the relevant information in the hand.
    def deal_cards(self, hand):
        if not self.shoe: #The shoe should never be empty, but if players reduce the max_hand variables or improperly calculate max hand value for custom games, this check could be necessary.
            self.add_to_shoe()
        new_card = self.shoe.pop()
        hand.cards.append(new_card)
        if new_card.rank == "A":
            hand.soft_aces += 1
        hand.total += new_card.value
        hand.demote_ace()

    #Validates input for yes or no questions.
    def get_yes_or_no(self, message):
        while True:
            pinput = input(message).lower().strip()
            if pinput in ["yes", "no", "y", "n"]:
                return pinput
            else:
                print("It's a yes or no question.")

    #Offers the players the ability to buy insurance if the dealer is showing an Ace. Insurance bets are always half the initial bet (varies by casino).
    def check_insurance(self):
        for p in self.players_list:
            if p.bankroll >= p.hands[0].bet / 2:
                choice = self.get_yes_or_no("Would {player} like to buy insurance? ".format(player = p.name))
                if choice in ["yes", "y"]:
                    p.hasInsurance = True
                    p.bankroll -= p.hands[0].bet / 2
            else:
                print("{player} does not have the funds to buy insurance.".format(player = p.name))
        if self.dealer.hands[0].isBlackjack:
            self.dealer.dealer_blackjack(self)
        else:
            print("The dealer does not have blackjack. The round continues.")

    #The dealer checks their hole card if they might have a blackjack.
    def dealer_start_round_checks(self):
        if self.dealer.hands[0].cards[0].rank == "A":
            self.check_insurance()
        if self.dealer.hands[0].isBlackjack:
            if self.dealer.hands[0].cards[0].rank != "A":
                self.dealer.dealer_blackjack(self)
            return False #Ends the round if the dealer has a blackjack (after insurance logic if the upcard is an Ace).
        return True #If the dealer does not have blackjack, the round continues.

    def player_turn(self, player):
        for h in player.hands:
            while not h.locked:
                if h.firstTurn:
                    h.print_hand()
                    if h.isBlackjack:
                        print("\033[32m{player} has a blackjack!\033[0m".format(player = player.name))
                        h.locked = True
                    else:
                        #Shows the dealer's upcard at the start of each player's turn so they can make informed decisions without having to scroll up to the outcome of the initial deal.
                        self.dealer.show_upcard()
                if not h.isBlackjack:
                    valid_options = h.create_action_list(self) #Creates a list of valid options based on the current state of the hand.
                    player_message = h.create_message(valid_options) #Creates a message for the player based on the player's available actions.
                    player_action = player.get_player_input(valid_options, player_message) #Gets the player's choice
                    h.resolve_action(player_action, self) #Executes the player's choice

    #Checks to see if all players have busted out (and thus the dealer's turn can be skipped)
    def bust_check(self):
        for p in self.players_list:
            for h in p.hands:
                if not h.isBust:
                    return True #The dealer takes their turn.
        return False #Skips the dealer's turn if all hands are bust.

    #Iterates through each hand and pays out the winners.
    def settle_round(self):
        for p in self.players_list:
            for h in p.hands:
                h.settle(self.dealer)

    #Handles end-of-round cleanup, removing players from the game who have gone broke, clearing out player hands, and subtracting the total value of cards dealt to players this round from the value of cards in the shoe.
    def round_cleanup(self):
        players_to_remove = []
        hands_total = 0
        for p in self.players_list:
            for h in p.hands:
                hands_total += h.total
            p.clear_round() #Resets player information to default and clears out their hands.
            if p.bankroll < 1:
                choice = self.get_yes_or_no("{player} has gone broke. Rebuy? ".format(player = p.name))
                if choice in ["yes", "y"]:
                    print("{player} rebuys into the game for ${amount}.".format(player = p.name, amount = self.buy_in))
                    p.bankroll += self.buy_in
                else:
                    print("{player} leaves the table after going broke.".format(player = p.name))
                    players_to_remove.append(p)
        self.remove_player(players_to_remove) #Removes players that have gone broke.
        hands_total += self.dealer.hands[0].total
        self.dealer.clear_round() #Clears the dealer's hand and sets it back to default.
        self.shoe_value -= hands_total #Updates the total value of cards left in the shoe to determine if a new deck needs to be added.

    def __repr__(self):
        return "Casino name: {casino_name}, Base deck: {deck}, Total card value in base deck (A at 1): {deck_value}, current shoe: {shoe}, shoe value at start of hand: {shoe_value}, active players: {players}.\nCasino rules:\nNumber of decks: {decks}\nMax players: {max_players}\nMax hands per player: {max_hands}\nSurrenders allowed: {surrender}".format(casino_name = self.casino_name, deck = self.deck_list, deck_value = self.deck_value, shoe = self.shoe, shoe_value = self.shoe_value, players = self.players_list, decks = self.decks, max_players = self.max_players, max_hands = self.max_hands, surrender = str(self.surrender_allowed))

#The Card class holds relevant information about each card in the deck.
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit #In standard rules, this is irrelevant. But users may want to make custom rules (such as a suited blackjack paying 3x or a custom "3 card flush" side bet) or utilize the Card class for games where a card's suit is relevant.
        self.card = rank + suit
        if rank in "AJQK":
            if rank == "A":
                self.value = 11
            else:
                self.value = 10
        else:
            self.value = int(rank)
        
    def __str__(self):
        return self.card

    def __repr__(self):
        if self.rank != "A":
            return "{card} has a value of {value}.".format(card = self.card, value = self.value)
        else:
            return "{card} has a maximum value of {value}, but can be demoted to a value of 1.".format(card = self.card, value = self.value)

#The Player class holds all the relevant information and functions related to individual players as well as to the dealer.
class Player:
    def __init__(self, name, game):
        self.name = name
        self.bankroll = game.buy_in
        self.hands = []
        self.hasInsurance = False

    #Validates a player's bet for their initial hand, returns -1 if they choose to leave the table.
    def betting(self, bet_string):
        if bet_string.lower().strip() == "leave":
            print("{player} left the table with ${money} remaining.".format(player = self.name, money = self.bankroll))
            return -1
        elif bet_string.isnumeric():
            bet_amount = int(bet_string)
            if bet_amount > self.bankroll:
                print("You don't have that much left!")
                return 0
            elif bet_amount == 0:
                print("{player} left the table with ${money} remaining.".format(player = self.name, money = self.bankroll))
                return -1
            else:
                return bet_amount
        else:
            print("Please enter a valid amount.")
            return 0

    #Shows the dealer's upcard.
    def show_upcard(self):
        print("Dealer's upcard: {upcard}".format(upcard = self.hands[0].cards[0]))

    #Handles payouts if the dealer has a blackjack.
    def dealer_blackjack(self, game):
        game.dealer.hands[0].print_hand()
        print("The dealer has blackjack!")
        for p in game.players_list:
            if p.hands[0].isBlackjack:
                message = "{player} has blackjack!".format(player = p.name)
                if p.hasInsurance:
                    message += " {player}'s hand is a push, but their insurance bet pays off.".format(player = p.name)
                    p.bankroll += p.hands[0].bet * 2.5
                else:
                    message += " The hand is a push."
                    p.bankroll += p.hands[0].bet
                print(message)
            else:
                if p.hasInsurance:
                    print("{player}'s insurance bet pays off.".format(player = p.name))
                    p.bankroll += p.hands[0].bet * 1.5
                else:
                    print("{player} loses.".format(player = p.name))

    #Gets and validates a player's input for the action they wish to take.
    def get_player_input(self, action_list, message):
        while True:
            pinput = input(message).lower().strip()
            if pinput in action_list: #Only accepts input from the list of valid actions.
                return pinput
            else:
                print("That is not a valid selection.")
    
    #Determines if a player can split, exists for redundant checks at the start of the split() function.
    def can_split(self, hand, game):
        if self.bankroll < hand.bet:
            print("Not enough funds!")
            return False
        if hand.cards[0].rank != hand.cards[1].rank:
            print("Hand cannot be split!")
            return False
        if len(self.hands) >= game.max_hands:
            print("{player} cannot have any more hands!".format(player = self.name))
            return False
        return True

    #Splits a player's hand. By default, a player can only have 2 hands, but the function is written with multiple splits in mind.
    def split(self, current_hand, game):
        if not self.can_split(current_hand, game): #This should never return False, but exists for redundancy.
            return
        splitting_hands = [current_hand] #List of the hands being adjusted in the function.
        splitting_hands.append(Hand((len(self.hands) + 1), self))
        self.hands.append(splitting_hands[1])
        self.bankroll -= splitting_hands[0].bet
        splitting_hands[1].bet = splitting_hands[0].bet
        if splitting_hands[0].cards[1].rank == "A": #Handles the special case of splitting Aces.
            splitting_hands[0].soft_aces = 1
            splitting_hands[1].soft_aces = 1
            splitting_hands[0].total -= 1
        else:
            splitting_hands[0].total -= splitting_hands[0].cards[1].value
        splitting_hands[1].cards.append(splitting_hands[0].cards.pop(1))
        splitting_hands[1].total = splitting_hands[1].cards[0].value
        for h in splitting_hands:
            game.deal_cards(h)
            h.print_hand()
            h.check_blackjack()

    #Handles the dealer turn logic. Future versions will have customizeable dealer stand values.
    def dealer_turn(self, game):
        valid_game = game.bust_check()
        if valid_game:
            self.hands[0].print_hand()
            while not self.hands[0].locked:
                if self.hands[0].total < 17:
                    print("Dealer takes a card.")
                    self.hands[0].hit(game)
                else:
                    self.hands[0].stand()
    
    #Resets round-specific variables to their defaults.
    def clear_round(self):
        self.hasInsurance = False
        self.hands = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{name} has a current bankroll of {bankroll}, currently playing {num_hands} hands: {hands}. Do they have insurance? {insurance}".format(name = self.name, bankroll = self.bankroll, num_hands = len(self.hands), hands = self.hands, insurance = self.hasInsurance)

#The Hand class holds all the relevant information and functions related to each players' hands.
class Hand:
    def __init__(self, id, player):
        self.player = player #The player playing the hand, important for some functions.
        self.id = id #If the player has more than one hand, this differentiates between the multiple hands.
        self.cards = []
        self.total = 0
        self.soft_aces = 0 #The number of soft Aces in a hand. When an Ace goes from a soft Ace (11 value) to a hard Ace (1 value), this is reduced.
        self.bet = 0
        self.locked = False #A hand is locked when it can take no more cards.
        self.firstTurn = True #Double, split, and surrender are only available on the first turn, and only a first turn hand can be a blackjack.
        self.isBlackjack = False
        self.isBust = False #Automatic loss

    #Turns a soft Ace (11 value) into a hard Ace (1 value) if the player's hand is over 21 and they have a soft Ace.
    def demote_ace(self):
        while self.total > 21 and self.soft_aces > 0:
            self.total -= 10
            self.soft_aces -= 1

    #Checks if a hand is a blackjack.
    def check_blackjack(self):
        if self.total == 21 and len(self.cards) == 2: #This function should only be called when the second half is true, but checking for 2 cards in hand helps to avoid bugs if this function is called when a hand has more than 2 cards.
            self.isBlackjack = True

    #Shows the player hand. If the player has more than one hand, it differentiates between the two with the hand ID.
    def print_hand(self):
        if len(self.player.hands) > 1:
            print("{player}'s hand {id}: {hand}".format(player = self.player.name, id = self.id, hand = self))
        else:
            print("{player}'s hand: {hand}".format(player = self.player.name, hand = self))

    #Creates a list of valid actions for a particular hand.
    def create_action_list(self, game):
        actions = ["hit", "stand"]
        if self.firstTurn and self.player.bankroll >= self.bet:
            if self.cards[0].rank == self.cards[1].rank and len(self.player.hands) < game.max_hands:
                actions.append("split")
            actions.append("double")
        if self.firstTurn and game.surrender_allowed:
            actions.append("surrender")
        return actions

    #Creates a message that gives the player a list of options based on the valid actions for a hand.
    def create_message(self, valid_actions):
        message = "Will {player} ".format(player = self.player.name)
        for a in valid_actions:
            if a == valid_actions[-1]:
                if len(self.player.hands) > 1:
                    message += "or {action} for hand {id}? ".format(action = a, id=self.id)
                else:
                    message += "or {action}? ".format(action = a)
            elif len(valid_actions) == 2:
                message += "{action} ".format(action = a)
            else:
                message += "{action}, ".format(action = a)
        return message

    #Calls the relevant function based on the player's choice.
    def resolve_action(self, action, game):
        if self.firstTurn and action != "split": #Makes doubling, splitting, and surrendering invalid after a hand's first turn. Replace with a len(cards) check in future versions. These are valid actions after splitting, however.
            self.firstTurn = False
        if action == "hit":
            print("{player} takes a card.".format(player = self.player.name))
            self.hit(game)
        elif action == "stand":
            self.stand()
        elif action == "double":
            print("{player} doubles down, risking it all on one more card!".format(player = self.player.name))
            self.doubling(game)
        elif action == "split":
            self.player.split(self, game)
        elif action == "surrender":
            print("{player} surrenders, forfeiting ${half}.".format(player = self.player.name, half = (self.bet / 2)))
            self.surrender()
        else:
            print("Error")

    #Handles hitting.
    def hit(self, game):
        game.deal_cards(self)
        if self.player in game.players_list: #Handles hitting differently if the individual hitting is a player or dealer. May be moved to separate functions in future versions.
            self.print_hand()
            if self.total >= 21: #Locks the hand if the hand reaches or exceeds max value (21) and labels the hand as busted if it goes over 21.
                if self.total > 21:
                    self.locked = True
                    self.isBust = True
                    print("\033[31m{player} busts out!\033[0m".format(player = self.player))
                else:
                    self.stand()
        else:
            self.print_hand()
            if self.total >= 17: #Dealer stands at 17.
                if self.total > 21:
                    self.locked = True
                    self.isBust = True
                    print("\033[32mDealer busts! All players win!\033[0m")
                else:
                    self.stand()

    #Handles doubling.
    def doubling(self, game):
        self.player.bankroll -= self.bet
        self.bet += self.bet
        self.hit(game)
        if self.total < 21:
            self.stand()

    #If surrenders are allowed, players can forfeit half their bet to guarantee a loss.
    def surrender(self):
        self.player.bankroll += self.bet / 2
        self.bet = self.bet / 2
        self.locked = True
        self.isBust = True #A surrender is technically a player declaring their hand to be "bust" before exceeding 21.

    #Locks the hand and gives the hand value.
    def stand(self):
        print("\033[34m{player} stands at {total}.\033[0m".format(player = self.player.name, total = self.total))
        self.locked = True

    #Settles the bets for each hand.
    def settle(self, dealer):
        self.print_hand()
        if dealer.hands[0].isBust and not self.isBust: #If the dealer goes bust, all non-busted hands win.
            if self.isBlackjack:
                print("{player} wins with a blackjack, winning ${amount}!".format(player = self.player.name, amount = (self.bet * 1.5)))
                self.blackjack()
            else:
                print("{player} wins ${bet}!".format(player = self.player.name, bet = self.bet))
                self.win()
        elif not self.isBust: #If neither the dealer nor the player hand are bust, whoever is higher wins.
            if self.total > dealer.hands[0].total:
                if self.isBlackjack:
                    print("{player} wins with a blackjack, winning ${amount}!".format(player = self.player.name, amount = (self.bet * 1.5)))
                    self.blackjack()
                else:
                    print("{player} wins ${bet}!".format(player = self.player.name, bet = self.bet))
                    self.win()
            elif self.total == dealer.hands[0].total: #If both hands have the same value, the hand is a push. Applies even if the player has blackjack.
                print("{player}'s hand is a push.".format(player = self.player.name))
                self.push()
            else: #If the dealer's hand has a higher value than the player's hand and neither are bust, the player loses.
                print("{player} loses their ${bet} bet.".format(player = self.player.name, bet = self.bet))
        else: #If the player is bust (or surrenders), they automatically lose.
            print("{player} loses their ${bet} bet.".format(player = self.player.name, bet = self.bet))

    #These methods handle the logic and calculations for different payouts.
    def blackjack(self):
        self.player.bankroll += self.bet * 2.5
    
    def win(self):
        self.player.bankroll += self.bet * 2

    def push(self):
        self.player.bankroll += self.bet

    def __str__(self):
        hand_string = " ".join(str(c) for c in self.cards)
        return hand_string

    def __repr__(self):
        return "Player: {player}, Hand ID: {id}, cards: {cards}, total: {total}, soft Aces: {soft_aces}, current bet: {bet}\nCurrent hand states:\nLocked? {locked}\nFirst Turn? {firstTurn}\nBlackjack? {blackjack}\nBusted? {bust}".format(player = self.player, id = self.id, cards = self.cards, total = self.total, soft_aces = self.soft_aces, bet = self.bet, locked = self.locked, firstTurn = self.firstTurn, blackjack = self.isBlackjack, bust = self.isBust)

game_state = GameState() #Initializes the table.
game_state.display_welcome()
game_state.create_players() #Creates a list of players and gets their names.
while len(game_state.players_list) > 0: #If there are no players, the game ends.
    game_state.check_shoe_size() #If there is a risk the current shoe will empty mid-round, adds decks to the shoe.
    game_state.initial_deal() #Betting and initial round of cards.
    if len(game_state.players_list) == 0: #Ends the game if all players choose to leave the table.
        break
    if game_state.dealer_start_round_checks(): #Dealer checks their hole card if they have an Ace or 10-value as their upcard. Skips the round if the dealer has a blackjack.
        for p in game_state.players_list:
            game_state.player_turn(p)
        game_state.dealer.dealer_turn(game_state)
        game_state.settle_round()
    game_state.round_cleanup() #Clears hands and round-specific data