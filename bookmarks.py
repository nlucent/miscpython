#!/usr/local/bin/python

# Load all data from the Google Chrome Bookmarks file
# root level for bookmarks is ['roots']
# Bookmark bar is ['roots']['bookmark_bar']['children']
# Other bookmarks are located @ ['roots'] and ['roots']['other']

bookmark_file = '/Users/nlucent/Library/Application Support/Google/Chrome/Default/Bookmarks'

# These contain all the objects found in the bookmark file
bookmark_bar_folders = []
bookmark_bar_links = []
bookmark_folder_folders = []
bookmark_folder_links = []

def loadChromeBookmarkFile(bookmark_file):

    bookmark_root = eval(open(bookmark_file).read())
    bookmark_bar = bookmark_root['roots']['bookmark_bar']
    bookmark_folder = bookmark_root['roots']['other']

    # First we roll over every entry to sort links and folders
    bookmark_folder_children = bookmark_folder['children'] # List
    bookmark_bar_children = bookmark_bar['children']

    for curDict in bookmark_folder_children:
        if curDict['type'] is 'url':
            #print "Found URL %s" % curDict['url']
	    bookmark_folder_links.append(curDict)
        elif curDict['type'] is 'folder':
	    #print "Found Folder named %s" % curDict['name']
	    bookmark_folder_folders.append(curDict)

    for curDict in bookmark_bar_children:
        if curDict['type'] is 'url':
	    #print "Found URL %s" % curDict['url']
	    bookmark_bar_links.append(curDict)
        elif curDict['type'] is 'folder':
	    #print "Found Folder %s" % curDict['name']
	    bookmark_bar_folders.append(curDict)

    # all items
    bookmark_bar_folders.

# Print names of each item in bookmarkList
def printNames(bookmarkList, number = True):

    j = 1
    for i in bookmarkList:
	if number is True:
       	    print "%d. %s" % (j, i['name'])
	    j += 1
	else:
	    print i['name']

# Print URLs for all items in bookmarkList
def printURLs(bookmarkList, number = True):

    j = 1
    for i in bookmarkList:
        if number is True:
	    print "%d. %s" % (j,i['url'])
	    j += 1
	else:
	    print i['url']


