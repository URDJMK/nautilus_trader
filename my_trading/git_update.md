# 1. Get the latest updates from the official repo
git fetch upstream

# 2. Update your local develop branch
git checkout develop
git merge upstream/develop

# 3. (Optional) Update your feature branch with the latest changes
git checkout BBprediction
git merge develop