## Advanced Browser
[Link to add-on on AnkiWeb](https://ankiweb.net/shared/info/874215009).

Advanced Browser is an Anki add-on that adds more features to the browser. It allows you to add a variety of new, sortable columns to the card browser. These columns range from:
- Fields from your note types
- Additional statistics about the cards
- Internal database values (if you're a developer; off by default)

![Note fields](https://raw.github.com/hssm/advanced-browser/master/docs/screenshot_info.png)

### Feature notice

The **note browser mode (show a single card per note)** for Anki versions 2.1.24-2.1.44 has been moved to a separate add-on maintained by another developer (@Arthur-Milchior). If you rely on this feature, you can download the add-on [Browser have one line by note](https://ankiweb.net/shared/info/797076357) from ankiweb (GitHub: [anki-browser-for-note](https://github.com/Arthur-Milchior/anki-browser-for-note)). A "notes only" mode is built into Anki 2.1.45 or newer.

### How to use
Right click on any of the currently visible columns and a menu will appear. Some new menu items will now appear in the list.

- The **- Fields -** menu item contains a list of your note types. Each note type reveals a sub-menu with each of its fields that can be enabled as columns. If a field name exists in another note type, it will be enable as well, and sorting by this column will consider all of the note types together as one:<br>![Useful columns](https://raw.github.com/hssm/advanced-browser/master/docs/context_note.png)

- If you prefer to see every field in a single list instead of grouping fields by note type, you can toggle the behaviour by editing the configuration item `Use a single list for fields` using Anki's add-on manager and setting it to `true`:<br>![Useful columns](https://raw.github.com/hssm/advanced-browser/master/docs/context_flat.png)

- The **- Advanced -** menu item offers some columns with interesting statistics about each card.<br>![Useful columns](https://raw.github.com/hssm/advanced-browser/master/docs/context_stats.png)

### Copying table content
By setting `"Table content"` to `"Selectable"`, you'll be able to select table content by double clicking on it. This way, you can copy it. Note that editing the content has no effect.

### Editing the table
By setting `"Table content"` to `"Editable"` you can edit the content of *some* elements of the tables. You need to activate this feature in the configuration before being able to use it. It can be dangerous if you don't really know what you're doing and this feature is not widely used and tested. Please see the document [edition in table](edition in table.md) to see what editing each column does.

### Internal fields
You can also show some fields used internally by Anki but probably aren't very useful for the typical user. These are disabled by default, but you can enable them in the add-on config by setting `"Show internal fields"` to `true`. 

## Help and suggestions

#### New column?
If you have a good idea for a new column, please open a new issue on GitHub. If you are a developer and would like to add it yourself, please see `advanced_fields.py` as it's the most likely place you'd want to put it. Contributions are more than welcome!

#### Add-on author?
If you are an add-on author and would like to add a new column in your own add-on, then doing so is easy through Advanced Browser. Advanced Browser is designed to let add-ons add their own columns through a standard Anki hook. In fact, Advanced Browser uses this same hook to offer its own columns, so you already have a working example to look at. Your own add-on can easily add its own columns provided your user also has Advanced Browser installed.
