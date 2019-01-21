## Advanced Browser
[Link to add-on on AnkiWeb](https://ankiweb.net/shared/info/874215009).

An Anki add-on that adds advanced features to the card browser. This add-on is licensed under GPLv3.


---

Advanced Browser is an Anki add-on that aims to add useful features or enhance the usability of the card browser. Below is a list of features available at the moment.

### Note fields as columns
This allows the addition of **any** field in your decks as a column that you can display and sort. This means you can have more than just ```Sort Field``` as a usable column. You need to right-click the column bar to bring up the list of available columns.

![Note fields](https://raw.github.com/hssm/advanced-browser/master/docs/screenshot_info.png)


You can edit the configuration (using add-on manager) to see every single fields in a single context menu. You only have to change the option "Each fields in a single list" to ```true```.

### More useful columns

You can also add these extra columns:
- First review date
- Latest review date
- Average answer time
- Total answer time
- Tags

![Useful columns](https://raw.github.com/hssm/advanced-browser/master/docs/context.png)

### Note browser mode (show a single card per note type)

There is now a menu option to **Only show notes**. If you are only interested in editing the content of notes and don't care about the statistics of individual card reviews, you can enable the note browser mode.

When this option is enabled, the browser will show a single row for each note regardless of how many cards a note may have generated. You can use *Ctrl+Alt+N* as a shortcut to toggle this option.  (Pay attention to the fact that buttons, such as «suspend», act on cards and not on notes. Therefore, avoid using this button while you use the option to see notes.)

![Note browser mode](https://raw.github.com/hssm/advanced-browser/master/docs/note_browser_toggle.png)

### Internal fields
You can also show some fields used internally by Anki but probably aren't very useful for the typical user. These are disabled by default, but you can enable them by going to **Tools -> Add-ons -> advanced_browser -> Edit...** and uncommenting the line that loads the extension that offers those fields.

![Internal fields](https://raw.github.com/hssm/advanced-browser/master/docs/edit.png)
![Internal fields](https://raw.github.com/hssm/advanced-browser/master/docs/context_internal.png)

---
## Help and suggestions

#### New column?
If you have a good idea for a new column, please open a new issue on GitHub and I will likely include it. If you are a developer and would like to add it yourself, please see ```custom_fields.py``` as it's the most likely place you'd want to put it. Contributions are more than welcome!

#### Add-on author?
If you are an add-on author and would like to add a new column in your own add-on, then doing so is easy through Advanced Browser.

Advanced Browser is designed to let add-ons add their own columns through a standard Anki hook. In fact, Advanced Browser uses this same hook to offer its own columns, so you already have a working example to look at. Your own add-on can easily add its own columns provided your user also has Advanced Browser installed.
