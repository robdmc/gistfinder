# gistfinder
Here is what gistfinder does

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
   gistfinder -t your_personal_access_token
   ```


![Diagram](images/gh_instructions.png)
