# shuttleDrop - One-Touch File Uploading

I just wanted a dead-simple way to drop files to another computer. 
So I made one in Python and FastAPI. 

In under 30 seconds, you can have a simple webpage running that puts uploads in any folder you choose.

## How To Use It
1. Clone this repo
2. Edit `docker-compose.yml` and point it at the directory you want files uploaded to
3. `docker compose up`
4. Go to `http://your-ip:8000/` from another computer and drop files on the page

That's it. 

## Security 

This app runs in Docker and mounts the upload directory into that container.
This should be more than secure enough for most use cases. 

In theory, if there's a bug in shuttleDrop or FastAPI, someone could read all the files in that directory. 
So you should not pick a directory that already contains sensitive files.

If you're exposing shuttleDrop to the Internet, you might want to put a real httpd like `nginx` in front of it and enable TLS.