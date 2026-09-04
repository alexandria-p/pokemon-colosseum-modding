* Requires cloning https://github.com/StarsMmd/GoD-Tool to the root directory (I cloned mine to a folder called 'Pokemon Colosseum - GoD-Tool by Stars' and added it to my .gitignore)
* Recommended use Claude Pro and Opus 5 model


## Acknowledgements:
* Maps from https://github.com/StarsMmd/Colo-XD-PBR-symbol-maps, and may be outdated
* Offsets and gecko/ar codes from Ralf at gc-forever (via Wayback Machine)
* Thank you Stars for being the backbone of the GC Pokemon modding community
* Thank you GameBeast92 for introducing yourself and being so generous with sharing your modding workflow ⭐

## Advice and Tips in Dolphin:
Never do an in-Dolphin memory value search — it hangs Dolphin. Instead ask for Memory → Export → Dump MRAM and analyse the .raw (the path is under Options → Configuration → Paths → Dump Path).
PkHeX check: set Options → GameCube → Device Settings → Slot A to GCI Folder; save at an in-game PC to the Slot A card; in Dolphin Tools → Memory Card Manager open the card, delete any existing Colosseum save, Import the latest .gci; then open the memory-card file in PkHeX.
Dolphin breakpoints can either be 'memory' breakpoints (when a memory address is read or written-to), or 'instruction' breakpoints (when assembly code/'instruction' is hit)

## Shiny Breakpoints
US Rom: Only fires when shiny is set to TRUE for PID
Instruction Breakpoint
Address: 0x801FA3EC
Condition: r6 == 1

## Save-relative addresses:
* Get Claude to re-read the save-base pointer at the start of every session and recompute everything from it.
	
Start here: Save-base pointer global	
| US	| 0x8047ADB8 |
| PAL	| 0x804C8268 |

Open the Memory panel in Dolphin and read the big-endian 32-bit word at that address. That word is the save base.  (Example values seen: US 0x804085E0, PAL 0x804559E0)

* Recalculate every save-relative address below from the base you just read.

## Clearing up misconceptions around Shiny logic in Pokemon Colosseum:

ADDITIONAL INFORMATION ON HOW SHINIES ARE CALCULATED IN POKEMON COLOSSEUM (ADVANCED):
PID - Pokemon ID
TID - Trainer ID
SID - Savefile ID

Calculating if a pokemon is a 'shiny' in Pokemon Colosseum is done with a mathematical formula.
Shiny if: (TID/SID ^ FIRST_HALF_OF_PID ^ SECOND_HALF_OF_PID) < 8

So what causes the visual 'bug' or shiny appearance of a pokemon to change in Pokemon Colosseum?
1. Shadow PokÃ©mon PID is rolled on first encounter, and locked into save data.
2. Whenever the pokemon is displayed onscreen, their appearance is calculated at runtime (when the camera is on them in battle, or their profile picture is created for their in-battle HUD, or their profile picture is created for you to see when you look at switching to another pokemon in your party, or their full model is needed if you open their summary)
3. When their appearance is calculated, the 'Shiny mathematical formula' is checked, to confirm if the colors need to be shiny pokemon colors or not for the render.
4. But while the pokemon is still owned by the AI trainer, the 'Shiny mathematical formula' substitutes in the AI trainer's TID/SID data!
5. Once you snag the shadow pokemon, its trainer ID will be replaced with your trainer ID. 
6. From now on when their appearance is calculated, the 'Shiny mathematical formula' is checked but it now uses YOUR trainer TID/SID.
7. This means that (depending on the Pokemon's PID, the AI trainer's TID and your TID/SID), the same pokemon PID could display as shiny/not shiny for two different trainers. 

It could appear as:
a) Non-shiny for the AI trainer, but shiny for you. 
b) Non-shiny for the AI trainer, and also non-shiny for you. (sad)
c) ** Shiny for the AI trainer, but non-shiny for you. (heartbreaking)
d) ** Shiny for the AI trainer, and also shiny for you (tiny tiny tiny mathematical chance, but still possible!)

8. Now there is a caveat here. PID are not hardcoded for pokemon owned by trainers in Pokemon Colosseum - they are rolled at runtime. When a PID is rolled for a pokemon in Colosseum, it doesnt just roll a PID and move on. If the first PID rolled would be a 'shiny' against the enemy AI trainer's TID/SID (according to the 'Shiny mathematical formula'), the game will actually RE-ROLL the PID again. And again. Until it lands on a PID that is not-shiny for the enemy AI trainer - regardless of whether this is a snaggable or unsnaggable enemy pokemon.  Presumably, the developers did this so that they wouldn't bait poor players with un-snaggable shinies.

This means in the base Pokemon Colosseum, you actually will only ever encounter scenarios 7a) and 7b). You will /never/ encounter scenarios 7c) or 7d).
