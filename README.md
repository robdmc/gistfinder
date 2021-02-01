# Gistfinder
Gistfinder provides local terminal-based access to all your github gists.
You can fuzzy-search your gists and have them immediately available to you
for cut and paste into the terminal.

If you are familiar with the vim keybings (j-k for down-up and / for search) you should feel
right at home in gistfinder.

# Installation
```bash
pip install gistfinder
```

# Usage
You must first configure github to allow it access to your github account.
Doing so will store your github username and access token locally to
` ~/.config/gistfinder/github_auth.json`.  (See below for details)

## Sync your gists locally
To sync all your gists locally, simply run
```bash
gistfinder --sync
```
or use the shortcut alias
```bash
gf --sync
```
To blow away all local gists and resync
```bash
gf --reset
```

To start gistfinder, simply type
```
gistfinder
```
or
```
gh
```
This will open an interactive application in your terminal that looks like this

![Diagram](images/gistfinder_example.png)
The yellow text at the upper left is the description of the gist currently
selected in the grey area.  You can navigate this selection using vim-like j-k keys.

At any point you can press the space bar to move over to the code window and navigate your
code using vim keybindings.

To exit gistfinder at any time, you can use either `ctrl-c` or `ctrl-q`, whatever alignes better with your
muscle memory.

Much like vim, pressing the / key will drop you into a fuzzy search across all
your gists.  File names, descriptions and code contents are all indexed in the search.
As you search the file name list on the left will reorder itself to show the most
relevant file names at the top.  Pressing enter will get you out of search mode
and back into list navigation mode, but will continue to show search term that resulted
in the current list ordering.  When you have selected the filename of the gist you are
interested in, simply pressing `enter` will exit gistfinder with the contents of that gist
written to stdout.


# Configuration
Gistfinder will need permission from Github to access your gists.
The best way to set this up is to create a personal access token that
gistfinder can use to download your gists to your computer.

Here are the steps:

1. Choose "Settings" from your profile at the upper right corner of your Github home page.
1. Go to "Developer Settings"
1. Choose "Personal access tokens"
1. Generate a new token
1. Name the token something descriptive. Perhaps "gistfinder"
1. Limit the permissions to only have access to gist
1. Copy the created token to your terminal into the command
   ```bash
   gistfinder -u github_username -t your_personal_access_token
   ```
   And that's it!  You should now be ready to sync and search your gists



![Diagram](images/gh_instructions.png)

