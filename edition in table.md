This document consider the very question of editing the content of a
specific element in the browser's table. By default, most edition will
just be ignored. If an edition can't be understood it'll be ignored or
will raise a warning message explaining why the action can't be
done. 

Here is the list of edition which can be done.

# Deck
There are three decks values, "original deck", "current deck" and
"deck". If a card is filtered, the "deck" contains the current
(filtered) deck, and in parenthesis the original deck. Otherwise the
"deck" is equal to the "current deck" and the "original deck" is not
set. The edition can be made in the columns of original decks and
current decks (name and id), but not in the "deck" column.

## Current deck
Decks can be changed using:
* Deck name: If you enter an existing deck name (ignoring case and
  unicode normalization) then the card will be moved to this
  deck. Otherwise, it will ask whether you want to create the
  add-on. Note that this means that in case of cards in filtered deck,
  the default text won't be accepted as a correct edition.
* Deck id: You can only change the deck id to the id of a deck which
  already exists. 

A note about moving a card from standard to dynamic deck (either by
name or by id). In this case, a original deck will be set. Either the
current original deck if the card is already in a filtered deck, or
the current deck otherwise. The card will move as a priority card (Due
value -100000), and the original due will be set.

## Original deck
The original deck can be edited only if there is already an original
deck. Indeed, it would not be clear what would mean original deck if
there the current deck is not a filtered deck.

Changing the original deck name or id is done as for the current deck.

# Card type
* ord: A card can be positionned only to a valid value. For a note
  typi with cloze deletion, a valid value is any non-negative
  integer. Otherwise, it's a non-negative integer less than the number
  of card type. Note that card type are indexed starting at 0 here;
  e.g. the first card's ord is 0 and note 1.
* Card: The card name. It can only be changed to another card name of
  the same note type.
  
Note type can't be changed. This is because this process is far less
trivial. In particular when note type have a distinct number of
fields. 

# Others
* Tags: Edit tags, as in the editor, without auto-completion
* Ease: Put any easyness. Last % symbol can be present or
  omitted. Anything else than a number, potentially followed by a %
  symbol, will be ignored. 
* Note fields: The list of note fields, with a special character as a
  separator. On my computer this character is represented as a black
  rectangle. If your edition does not keep the correct number of
  fields, the edition will be ignored. Otherwise fields get
  updated. (Note that the separator is not the same here and in the
  database, the separator here is usually visible)
* Flags: represent as number, as in anki database, or as the english
  string representing the color.
  
# Internal
* Card Type : Those values should be given either as a number, in
  which case it should be the same as the number in anki data
  structure. Or as string, similar to the anki's code constant. "new",
  "lrn", "rev", "relearning" (only for scheduler v2 here)
* Card queue : Those values should be given either as a number, in
  which case it should be the same as the number in anki data
  structure. Or as string, similar to the anki's code
  constant. "manually buried", "subling buried", "suspended" "new",
  "lrn", "rev", "day learn relearn", "preview". 
* usn: I should emphasize that usn is set each time anki saves
  data in the collection, so the value you'll set will probably get
  reset anyway.
  
If you change one of those two values, you should probably change the
other one two, and potentially change the due value.
  
# Id:
Unless you know exactly what you do, changing an id, is probably a bad
idea. Anki may not recognize a card/note if the id is changed, and you
may ends with duplicate after synchronization. In order to limit
risks, if you change a note or card id, anki will tells the server
during synchronization that a note/card was deleted and another
created, so that other devices will believes those are distinct
notes/cards. This means in particular that any change and reviews made
on other devices will be lost.

Here are the particular of each ids:
* Globally unique id (guid): It's not clear whether changing the GUID
  may have any consequence. It seems to be only when notes/decks are
  exported and imported, to check whether an imported note is already
  in the collection.
* Note id: If you change a note id, all cards of this note will have
  their note id changed. There is currently no way to change the note
  to which a card is attached. If you ever need this feature, feel
  free to ask for it to arthur@milchior.fr.
* card id: If you change a card id, it will also change the the card
  id in all reviews will be updated, so that reviews log are still
  associated to the same card.

## Statistics
I should not in particular that no fields related to statistics can
be edited. Indeed, values such as "minimal/average review time", "first
review", etc... are not saved in the database but computed each time
they are displayed using the revlog (review log). I currently see no
reason to allow update of revlog.
