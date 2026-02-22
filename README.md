# Harbor Cleaner
Harbor cleaner is a program written in Python that delete image on Habor registry when receive a delete push event from GitLab WebHook.

When user send a delete push for a specific branch, the harbor cleaner delete all images in registry with the same tag name of the deleted branch, for example:

1- user delete a branch with the name test-branch

2- gitlab send the webhook to cleaner

3- the cleaner check the type of push

4- if push is a delete for branch, it filter all images with structure image-name:test-branch

5- cleaner delete filtered images
