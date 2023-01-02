### 2022-11-12

* initial push to github

* basic player movement and input

* icon assets

* abilities and hitboxes

### 2022-11-13

* more icon assets - trait icons

* ui icon alignment

* transformed from cartesian coordinates to isometric

* began work on the arm and wing model by transforming the existing leg model

### 2022-11-14

* added to isometric camera transform to include the z position of the creature (verticality)

* changed the way creature's legs bent by introducing verticality

### 2022-11-15

* updated skillshot ui and skillshot abiltiy activation to reflect user input

* updated player movement to match input

* both of these are fixes to problems related to isometric perspective

### 2022-11-16

* began giving creatures verticality

* creatures can stand upright based on leg positions

* plans to change how legs bend + get arms and wings positioned correctly

### 2022-11-17

* fixed leg joint and step calculations taking into account verticality

* fixed locations for arms + wing placement

### 2022-11-20

* fixed hitboxes for different attacks to take into account verticality

### 2022-11-21

* began working on the systems by which evolution will take place, like mutation and reproduction (currently just duplication)

### 2022-11-26

* evolution mechanics and systems

* get more body segments and legs

### 2022-11-27

* began building the ai system

* ai movement and tracking player

### 2022-11-28

* fixed some bugs with ai movement and mutation systems

* began building ai ability usage and attacking player

### 2022-12-27

* created ui/hud sprites

* changed main menu screen; created font + basic solar system model visual

### 2022-12-28

* gave enemies an internal cooldown on using abilities

* creatures now have idle movement (random movement)

* creatures now run away if they have a negative aggression score

* aggression score and herding score are shifted randomly each generation

### 2022-12-29

* began working on the foundations of the world quest system that allows players to make progress

* players will receive quests to unlock traits, abilities, and can upgrade stats / make allocations (go up a level)

* began work on ui pinging for new quests

### 2022-12-31

* made ui to view quests, card carousel type display

### 2023-01-01

* quest card carousel now displays all quests 

* players can accept quests

* players currently autocomplete quests

* players can upgrade stat/allocate stats/get traits/get abilities

* death screen and entity death

* began working on player interaction with corpses (dead entities)
