This is a copy of the offical pyramid tutorial. Since I had some issues to get
it running I cleaned it slightly up, such as moving the app to the app subdir
and now it just works with a very clean python using::
	
    /path/to/python2.7 bootstrap.py
    ./bin/buildout
    ./bin/dev_appserver app

And in your browser just point to ``http://localhost:8080``.

