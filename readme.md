This is a heavily commented example of how to use the evernote oauth API via python. 

Evernote's documentation doesn't describe the python library usage, just raw http calls (and is ambiguous for all that); they release sample applications using their library, and I worked off of that, to simplify and then include comments explaining what's going on.

This works, but isn't super-clean right now.  Will be rewritten as a tutorial/blog post in the future.

What this does: 

1.  spin up a local web server (via flask) and invite the user to go an authoriation webpage.
2.  redirect user to evernote authentication
3.  take it back and prove we've authenticated by displaying the username.
4.  Behind the scenes, do all the oauth shuck and jive.
