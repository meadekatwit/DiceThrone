import random

class Hero:
    """
    The "Player" class, holding all relevant information to a player.
 
    Attributes:
        name (str): The name of the Hero.
        health (int): The health of the Hero (Default to 50 in a 1v1 situation).
        dice (list of Dice objects): Player's Dice.
        abilities (list of Ability objects): Abilities avalible to the hero
        conditions (list of Condition objects): Conditions afflicting the hero
        cp (int): Combat points avalible.
        rolls (int): Number of rolls left
    """

    def __init__(self, health = 50, name = "Unnamed Hero", dice = [], abilities = [], conditions = [], cp = 2):
        global debug
        self.name = name
        self.dice = dice
        self.abilities = abilities

        for ability in self.abilities:
                ability.host = self
                for action in ability.actions:
                    #if debug: print (" === [{} Hero Object]: Initializing action [{}] in ability [{}]".format(self.name, action, ability.name))
                    action.dealer = self

        self.health = health
        self.conditions = conditions
        self.cp = cp
        self.rolls = 0

    def __str__(self):
        output = "Name: {}".format(self.name)
        output += "\nHealth: {}".format(self.health)
        output += "\nCombat Points: {}".format(self.cp)
        output += "\nConditions: "
        if self.conditions == []:
            output += "None--"
        for condition in self.conditions:
            output += condition.name + ", "

        output = output[:-2]
        return output

    def sortDice(self):
        newDice = []
        for i in range(7):
            for diceSegment in self.dice:
                if diceSegment.value == i:
                    newDice.append(diceSegment)
        self.dice = newDice

    def displayDice(self):
        output = ""
        self.sortDice()
        for dice in self.dice:
            output += str(dice) + ", "
        return output[:-2]

    def modifyHealth(self, amount, source, sourceType = ""):

        """
        Modifying health from an external source. If the damage is from an attack,
        it triggers a defense ability as well as any conditions affected by being damaged.

        Parameters:
            amount (int): Number to modify health.
            source (Hero): The source of the damage.
            sourceType (string): The type of damage source.
        """
        global debug, gameOutput

        if sourceType == "Attack":
            amount += self.triggerCondition("AttackDamage") #Implied to change attack modifier, current use is for Targeted

            defense = self.defenseAbility()
            if debug: print(" === [{} Hero Object]: Triggering defense ability {}.".format(self.name, defense.name))
            
            amount = defense.use(source, amount)
        
        elif sourceType == "UndefendableAttack":
            amount += self.triggerCondition("AttackDamage")

        if self.triggerCondition("DamageTaken") == 1: #Nullifies damage if triggered, current use is for Evasive
            amount = 0

        self.health = self.health + amount

        if debug: print(" === [{} Hero Object]: Changing health by {}.".format(self.name, amount))
        if gameOutput:
            if amount <= 0: print("{} lost {} health!".format(self.name, amount * -1))
            else: print("{} gained {} health!".format(self.name, amount))

    def addCondition(self, condition):
        global debug, gameOutput
        if debug: print(" === [{} Hero Object]: Attempting to add {} condition.".format(self.name, condition.name))

        stackLimit = condition.stackLimit
        stack = 0

        for subCondition in self.conditions:
            if subCondition.name == condition.name:
                stack += 1

        if stackLimit <= stack:
            if debug: print(" === [{} Hero Object]: Unable to add {} condition. Stack Limit: {}, Current Items: {}".format(self.name, condition.name, stackLimit, stack))
        else:
            if debug: print(" === [{} Hero Object]: Able to add {} condition. Stack Limit: {}, Current Items: {}".format(self.name, condition.name, stackLimit, stack))
            if gameOutput: print("{}: Recieved {} condition.".format(self.name, condition.name))
            self.conditions.append(condition)
    
    def removeCondition(self, condition):
        self.conditions.remove(condition)

    def defenseAbility(self):
        for ability in self.abilities:
            if ability.defense:
                return ability

    def findAbility(self, abilityName): #TODO: Change to give user option of defense roll possibly
        for ability in self.abilities:
            if ability.name == abilityName:
                return ability
            
        return self.abilities[-1] 
            
    def getValidAbilities(self, dice = []):
        if dice == []:
            dice = self.dice

        validAbilities = []
        for ability in self.abilities:
            if ability.checkValid(dice):
                validAbilities.append(ability)

        return validAbilities
            
    def triggerCondition(self, trigger):
        """
        Checks the specified trigger against the conditions associated with the Hero object.

        Parameters:
            trigger (str): The trigger to check against the conditions.

        Returns:
            int: The cumulative return key obtained from the triggered conditions.
        """

        #In retrospect, having conditions trigger based off a string is much more cumbersome than having them trigger at custom points, but that's a rework for the future.

        global debug
        if debug: print (" === [{} Hero Object]: Checking for conditions with {} trigger.".format(self.name, trigger))

        returnKey = 0

        for condition in self.conditions:
            if condition.trigger == trigger:
                if debug: print(" === [{} Hero Object]: Condition [{}] triggered.".format(self.name, condition.name))
                returnKey += condition.act()
                if not condition.persistent:
                    self.conditions.remove(condition)

        return returnKey

class Ability:
    def __init__(self, name = "Unnamed Ability", requirements = [], actions = [], defense = False, ultimate = False):
        self.name = name
        self.requirements = requirements
        self.actions = actions
        self.defense = defense
        self.host = ""
        self.ultimate = ultimate

    def __str__(self):
        output = ""
        output += "Ability Name: {}".format(self.name)
        if type(self.requirements) == list:
            output += "\nRequirements: {}".format(', '.join(map(str,self.requirements)))
        else:
            output += "\nRequirements: {} dice strait.".format(self.requirements)
        output += "\nActions: "
        for action in self.actions:
            output += "\n - {}".format(str(action))
            
        return output

    def checkValid(self, dice):
        global debug
        if debug: print(" === [{} Ability Object]: Checking for validity".format(self.name))

        if self.defense:
            return False

        if type(self.requirements) == int: #Check for Straits
            if self.requirements == 4:
                requirementLists = [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]]
            elif self.requirements == 5: 
                requirementLists = [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]]

            for requirementList in requirementLists:
                for diceValue in dice:
                    for requirement in requirementList:
                        if diceValue.value == requirement:
                            requirementList.remove(requirement)
                            break

                if requirementList == []:
                    return True
            
            return False

        else: #Check for Faces
            requirementList = self.requirements.copy()
            for diceValue in dice:
                for requirement in requirementList:
                    if diceValue.side == requirement:
                        requirementList.remove(requirement)
                        break

            return requirementList == []

    def use(self, target, amount = 0):
        global debug, gameOutput
        if debug: print(" === [Ability Object]: Using ability [{}] on {}.".format(self.name, target.name))
        if gameOutput: print("{}{}: Using {}ability {} on {}.".format(self.defense * "> ", self.host.name, self.defense * "defensive ", self.name, target.name))

        if self.defense:
            for action in self.actions:
                amount = action.act(source = target, damageRecieved = amount) 
        else:
            for action in self.actions:
                action.act(target = target)

        return amount

# ======== Actions
class Action:
    def __init__(self, dealer = ""):
        self.dealer = dealer

    def act(self, target):
        return "Acting on {}.".format(target.name)

class Damage(Action): #Deal Flat Damage
    def __init__(self, damage, dealer = ""):
        super().__init__(dealer)
        self.damage = damage
    
    def act(self, target):

        global debug
        if debug: print (" === [Damage Action Object]: Damaging {} to {}".format(str(self.damage), target.name))
        target.modifyHealth(-1 * self.damage, source = self.dealer, sourceType = "Attack")
        if debug: print (" === [Damage Action Object]: {} health: {}".format(target.name, target.health))
        
    def __str__(self):
        return "Deal {} damage.".format(self.damage)

class UndefendableDamage(Action): #Deal Flat Damage
    def __init__(self, damage, dealer = ""):
        super().__init__(dealer)
        self.damage = damage
    
    def act(self, target):

        global debug
        if debug: print (" === [Damage Action Object]: Damaging {} undefendable to {}".format(str(self.damage), target.name))
        target.modifyHealth(-1 * self.damage, source = self.dealer, sourceType = "UndefendableAttack")
        if debug: print (" === [Damage Action Object]: {} health: {}".format(target.name, target.health))
        
    def __str__(self):
        return "Deal {} undefendable damage".format(self.damage)

class Inflict(Action): #Inflict Condition
    def __init__(self, condition, dealer = ""):
        super().__init__(dealer)
        self.condition = condition

    def act(self, target):
        #if self.condition.givenToSelf:
        #    target = self.dealer
        target.addCondition(self.condition)
        self.condition.setOwner(target)

        global debug
        if debug: print (" === [Inflict Action Object]: Inflicting {} on {}".format(self.condition.name, target.name))

    def __str__(self):
        return "Inflict {}".format(self.condition.name)

class RollEffect_MoonElf(Action): #Inflict Effect based on Roll
    def __init__(self, dealer = ""):
        super().__init__(dealer)

    def __str__(self):
        return "Roll Effect"

    def act(self, target):
        global debug
        if debug: print (" === [RollEffect Action Object]: Rolling for effect.")

        damage = 3

        for dice in self.dealer.dice:
            dice.roll()

        for dice in self.dealer.dice:
            if debug: print(" === [RollEffect Action Object]: {} rolled.".format(dice.side), end = "")

            if dice.side == "Arrow" or dice.side == "Foot":
                damage += 1
                if debug: print(" adding 1 damage.")
            if dice.side == "Moon":
                if target.cp != 0:
                    target.cp = target.cp - 1
                if debug: print(" removing 1 cp.")
            
        if debug: print(" === [RollEffect Action Object]: dealing {} damage.".format(damage))
        target.modifyHealth(damage, "Attack")
        Inflict(Blind).act(target)

class MissedMe_MoonElf(Action): #"Missed Me" Effect
    """
    Defense roll, 5 Dice

    On 2 Foot, prevent 1/2 Damage, rounded up.
    For every 2 Arrow, deal 1 undefendable damage.
    """

    def __init(self, dealer = ""):
        super().__init__(dealer)

    def __str__(self):
        return "Roll Effect"

    def act(self, source, damageRecieved):
        global debug, gameOutput
        if debug: print (" === [MissedMe Action Object]: Rolling for effect.")

        outputDamage = 0
        useDice = self.dealer.dice

        for dice in useDice:
            dice.roll()
            #if debug: print(" === [RollEffect Action Object]: {} rolled.".format(dice.side))

        if gameOutput: print("> {}: Rolled: {}".format(self.dealer.name, self.dealer.displayDice()))

        #Block half damage if two feet are rolled
        condition = ["Foot", "Foot"] #TODO: Maybe make function to make dice checking more sussinct
        for dice in self.dealer.dice:
            for item in condition:
                if item == dice.side:
                    condition.remove(item)
                    break
        if condition == []:
            trueDamage = damageRecieved - damageRecieved // 2
            if debug: print(" === [MissedMe Action Object] Reduced taken damage from {} to {}.".format(damageRecieved, trueDamage))
            if gameOutput: print("> Half of incoming damage blocked!")
            damageRecieved = trueDamage

        #Deal 1 undefendable for every two arrows
        arrows = 0
        for dice in useDice:
            if dice.side == "Arrow":
                arrows += 1

        outputDamage = arrows // 2
        if debug: print(" === [MissedMe Action Object] Retaliating {} undefendable damage".format(outputDamage))
        if outputDamage > 0:
            if gameOutput: print("> {} damage retaliated!".format(outputDamage))
            UndefendableDamage(outputDamage, self.dealer).act(source)

        return damageRecieved
        

# ======== Conditions
    
class Condition:
    """
    Condition Object, triggers on trigger variable, afflicting its owner.

    Attributes:
        name (string): Name of condition
        trigger (string): Triggering event for condition
        persistent (boolean): State of whether or not condition is removed on use.
        stacklimit (integer): Limit of how many of the same conditions can be had on one hero.
        giventoSelf (boolean): When condition is inflicted or gained by the dealer.
        owner (Hero): The holder of the condition.

    Methods:
        setOwner(Hero): Sets the owner of the Condition to "Hero"
        act(): Runs custom code of trigger. Returns relevant informantion.
    """
    def __init__(self, name, trigger = "", persistent = False, stackLimit = 1, givenToSelf = False):
        self.name = name
        self.trigger = trigger
        self.persistent = persistent
        self.owner = ""
        self.stackLimit = stackLimit
        self.givenToSelf = givenToSelf

    def setOwner(self, owner):
        self.owner = owner

        global debug
        if debug: print (" === [{} Condition Object]: Setting owner to {}".format(self.name, owner.name))

    def act(self):
        return 0

class Targeted(Condition):
    """
    Negative Status Effect, Stack Limit: 1

    +2 Incoming Attck Damage

    When a player afflicted with this token is Attacked by an opponsnet, the incoming attack dmg is increased by 2.
    Attack Modifier. Persistent.
    """

    def __init__(self):
        super().__init__(name = "Targeted", trigger = "AttackDamage", persistent = True)
    
    def act(self): #Add 2 Damage
        global debug
        if debug: print (" === [{} Condition Object]: Modifying +2 damage to {}".format(self.name, self.owner.name))

        return -2 #Add to damage modifier

class Entangle(Condition):
    """
    Negative Status Effect, Stack Limit: 1

    Lose 1 Roll Attempt

    A player afflicted with this token gets 1 fewer roll attempts during their next offensive roll phase.
    At the conclusion of the roll phase, remove this token.
    """
    def __init__(self):
        super().__init__(name = "Entangle", trigger = "PreOffRoll")

    def act(self):
        global debug
        if debug: print(" === [{} Condition Object]: Subtracting 1 roll attempt from {}".format(self.name, self.owner.name))

        self.owner.rolls -= 1

        return 0

class Blind(Condition): 
    """
    Negative Status Effect, Stack Limit: 1

    On 1-2, fail Offensive Roll Phase

    The next time a player afflicted with this token concludes their offensive roll phase,
    they must remove it and roll one dice. On 1-2, their offensive roll phase fails and has no effect of any kind.
    """ #Changed to checking before offensive roll phase

    def __init__(self):
        super().__init__(name = "Blind", trigger = "PreOffRoll")

    def act(self):
        global debug, gameOutput

        if debug: print(" === [{} Condition Object]: 1/3rd chance of skipping the offensive roll of {}".format(self.name, self.owner.name))

        dice = self.owner.dice[0]
        dice.roll()
        
        if gameOutput: print("> {}: {} Rolled for blindness effect.".format(self.owner.name, dice.value))

        if dice.value <= 2:
            if debug: print(" === [{} Condition Object]: Offensive turn skipped.".format(self.name))
            if gameOutput: print("> {}: Offensive Roll Skipped!.".format(self.owner.name))
            return -418
        
        return 0

class Evasive(Condition):
    """
    Spend and Roll 1-2 Attack damage
    
    When a player with this token recieves damage, they may choose to spend it. If spent, roll 1 dice.
    If the outcome is 1-2, no damage is recieved. Multible tokens may be spent in an attempt to prevent the same source of damage.
    """ #Add "spend" conditional

    def __init__(self):
        super().__init__(name = "Evasive", trigger = "DamageTaken", stackLimit = 3, givenToSelf = True)

    def act(self):
        global debug
        if debug: print(" === [{} Condition Object]: 1/3rd chance of avoiding all damage when spent.".format(self.name, self.owner.name))

        self.persistent = True

        if gameOutput: 
            i = input("{} has an evasive condition. Would they like to use it to deflect incoming damage? (Y/N): ".format(self.owner.name))
            if i.lower == "n":
                return 0
        
        self.persistent = False
        dice = self.owner.dice[0]
        dice.roll()

        if gameOutput: print("> {}: {} Rolled for evasive effect.".format(self.owner.name, dice.value))

        if dice.value <= 2:
            if gameOutput: print("All damage avoided!")
            return 1
        return 0
# ========= Dice

class Dice:
    def __init__(self, sides = ["Side 1", "Side 2", "Side 3", "Side 4", "Side 5", "Side 6"]):
        self.value = 1
        self.sides = sides
        self.side = self.sides[self.value - 1]
        self.locked = False

    def roll(self):
        global debug

        if not self.locked:
            self.value = random.randint(1, 6)
            self.side = self.sides[self.value - 1]
            if debug: print(" === [Dice Object]: {} rolled.".format(str(self)))

    def setValue(self, value):
        self.value = value
        if value > 0 and value <= 6:
            self.side = self.sides[self.value - 1]
        else:
            self.side = "NULL"

    def __str__(self):
        if self.locked:
            return "<{} - {}>".format(self.value, self.side)
        return "[{} - {}]".format(self.value, self.side)

def consoleGame():
    global debug, gameOutput
    debug = False
    gameOutput = True

    with open("asciiart.txt", "r") as f:
        print(f.read())

    #Generate Dice for Moon Elf
    moonDice = []
    moonCloneDice = []
    for i in range(5):
        moonDice.append(Dice(["Arrow", "Arrow", "Arrow", "Foot", "Foot", "Moon"]))
        moonCloneDice.append(Dice(["Arrow", "Arrow", "Arrow", "Foot", "Foot", "Moon"]))

    #Add Moon Elf abilities
    longbow3 = Ability("Longbow 3", ["Arrow", "Arrow", "Arrow"], [Damage(4)])
    longbow4 = Ability("Longbow 4", ["Arrow", "Arrow", "Arrow", "Arrow"], [Damage(5)])
    longbow5 = Ability("Longbow 5", ["Arrow", "Arrow", "Arrow", "Arrow", "Arrow"], [Damage(7)])
    demisingShot = Ability("Demising Shot", ["Arrow", "Arrow", "Arrow", "Moon", "Moon"], [Inflict(Targeted()), Damage(4)])
    coveredShot = Ability("Covered Shot", ["Arrow", "Arrow", "Foot", "Foot", "Foot"], [Inflict(Evasive()), Damage(7)]) #TODO: Replace evasive
    explodingArrow = Ability("Exploding Arrow", ["Arrow", "Moon", "Moon", "Moon"], [RollEffect_MoonElf()])
    entanglingShot = Ability("Entangling Shot", 4, actions = [Inflict(Entangle()), Damage(7)])
    eclipse = Ability("Eclipse", ["Moon", "Moon", "Moon", "Moon"], [Inflict(Blind()), Inflict(Entangle()), Inflict(Targeted()), Damage(7)])
    blindingShot = Ability("Blinding Shot", 5, actions = [Inflict(Blind()), Inflict(Evasive()), Damage(8)]) #TODO: Replace blind
    missedMe = Ability("Missed Me", 0,  [MissedMe_MoonElf()], defense = True)
    lunarEclipse = Ability("Lunar Eclipse", ["Moon", "Moon", "Moon", "Moon", "Moon"], [Inflict(Evasive()), Inflict(Blind()), Inflict(Entangle()), Inflict(Targeted()), UndefendableDamage(12)], ultimate = True)

    moonAbilities = [longbow3, longbow4, longbow5, demisingShot, coveredShot, explodingArrow, \
                    entanglingShot, eclipse, blindingShot, missedMe, lunarEclipse]

    moonCloneAbilities = moonAbilities.copy()

    #Main Game Loop

    moonElf = Hero(name = "Good Moon Elf", dice = moonDice, abilities = moonAbilities, conditions = [])
    moonElfClone = Hero(name = "Evil Moon Elf", dice = moonCloneDice, abilities = moonCloneAbilities, conditions = [])

    players = [moonElf, moonElfClone]

    def printPlayers(players):
        print("\n" + "=" * 50 + "\n")
        for player in players:
            print(player + "\n")
        print("\n" + "=" * 50 + "\n")

    running = True
    currentPlayer = players[0]
    turncount = 0

    while running:

        #Upkeep
        #print("-" * 50)
        #print("UPKEEP")
        #print("-" * 50)

        #Income
        #print("-" * 50)
        #print("INCOME")
        #print("-" * 50)

        if turncount != 0:
            currentPlayer.cp += 1

        #Draw
        #print("-" * 50)
        #print("DRAW")
        #print("-" * 50)
        
        #Main Phase 1

        #Round Start
        print("=" * 50)
        print("ROUND {}, {}'s TURN".format(turncount // len(players), currentPlayer.name))
        print("=" * 50)

        i = 0
        for player in players:
            i += 1
            print("Player {}:".format(i))
            print("\n" + str(player) + "\n")
        print("=" * 50)    
        
        #print("-" * 50)
        #print("MAIN PHASE 1")
        #print("-" * 50)

        #Offensive Roll Phase
        print("-" * 50)
        print("OFFENSIVE ROLL PHASE")
        print("-" * 50)

        currentPlayer.rolls = 3
        for dice in currentPlayer.dice:
            dice.locked = False

        if currentPlayer.triggerCondition("PreOffRoll") == -418: #Trigger Pre-Offensive-Roll Condtions
            currentPlayer.rolls = 0

        while currentPlayer.rolls > 0:

            print("\n{}: Offensive Roll: ".format(currentPlayer.name), end = "")

            for dice in currentPlayer.dice:
                dice.roll()

            print(currentPlayer.displayDice())
            currentPlayer.rolls -= 1

            if(currentPlayer.rolls > 0):

                output = ""
                for ability in currentPlayer.getValidAbilities():
                    output += ability.name + ", "
                print("\nAvailable abilities: {}".format(output[:-2]))

                print("{} Possible Reroll{}.".format(currentPlayer.rolls, "s" * (currentPlayer.rolls != 1)))
                diceInput = input("Input Dice To Freeze / Unfreeze (Numbers 1-5): ") #TODO: Make easier for player
                for i in range(5):
                    if str(i + 1) in diceInput:
                        currentPlayer.dice[i].locked = not currentPlayer.dice[i].locked

        print()

        avalibleAbilities = currentPlayer.getValidAbilities()
        if avalibleAbilities == []:
            print("No avalibile abilities are possible.")
        else:
            print("Choose one of the following abilities: ")
            for i in range(len(avalibleAbilities)):
                print("{}. {}".format(str(i + 1), avalibleAbilities[i].name))

            try:
                abilityNum = int(input("Select Ability: ")) - 1
            except:
                abilityNum = 0
            print()
            avalibleAbilities[abilityNum].use(players[(turncount + 1) % len(players)])

        #Defensive Roll Phase
            
        #Main Phase 2
        #print("-" * 50)
        #print("MAIN PHASE 2")
        #print("-" * 50)
            
        #Discard Phase
        #print("-" * 50)
        #print("DISCARD")
        #print("-" * 50)

        for player in players:
            if player.health <= 0:
                running = False

        turncount += 1
        currentPlayer = players[turncount % len(players)]

consoleGame()