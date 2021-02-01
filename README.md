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
You must first configure gisthub to allow it access to your github account.
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

## Search your gists
Simply type
```
gistfinder
```
or
```
gh
```



# Configuration
Gistfinder will need permission from Github to access your gists.
The best way to set this up is to create a personal access token that
gistfinder can use to download your gists to your computer.

Here are the steps:

1. Choose "Settings" from your profile at the upper right corner of you Github home page.
1. Go to "Developer Settings"
1. Choose "Personal access tokens"
1. Generate a new token
1. Name the token something descriptive. Perhaps "gistfinder"
1. Limit the permissions to only have access to gist
1. Copy the created token to your terminal into the command
   ```bash
   gistfinder -u github_username -t your_personal_access_token
   ```



![Diagram](images/gh_instructions.png)


To sync all of your gists
```bash
gistfinder --sync
```
or
```bash
gf --sync
```

To blow away all local gists and resync
```bash
gf --reset
```

