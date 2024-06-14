#!/usr/bin/python
from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import os

dropdir = os.path.join("..", "uploads")
disallowed_chars = r'<>:"/|?*'

# Ensure the uploads directory exists in the parent directory
os.makedirs(dropdir, exist_ok=True)

app = FastAPI()


class Settings(BaseSettings):
    port: str = os.getenv('PORT', '8000')
    maxUploadSize: int = os.getenv('MAX_UPLOAD_SIZE', 100)
    maxDirectorySize: int = os.getenv('MAX_DIR_SIZE', 10)
    overwriteWhenFull: bool = os.getenv('OVERWRITE_WHEN_FULL', False)

class ServerStatusModel(BaseModel):
    maxUploadSize: int = Field(description="The maximum size of each file, in megabytes")


def get_directory_size(path):
    total_size = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                except OSError:
                    pass
            elif entry.is_dir():
                total_size += get_directory_size(entry.path)
    return total_size


@app.on_event("startup")
async def startup_event():
    global settings
    settings = Settings()

@app.post("/api/upload")
async def upload_files(request: Request):
    form = await request.form()
    responses = []

    max_upload_size_bytes = settings.maxUploadSize * 1024 * 1024
    max_directory_size_bytes = settings.maxDirectorySize * 1024 * 1024 * 1024

    current_directory_size = get_directory_size(dropdir)

    for key in form:
        file: UploadFile = form[key]

        # tfw most of this applications' code is antiskid checks

        # Call out skiddery
        if '../' in file.filename:
            responses.append({"filename": file.filename, "status": "failed", "error": "Kill yourself"})
            continue

        # Replace disallowed characters in filename
        sanitized_filename = ''.join('_' if c in disallowed_chars else c for c in file.filename)
        file_location = os.path.join(dropdir, sanitized_filename)

        # Ensure the final path is inside the uploads directory
        if not os.path.commonpath([dropdir, file_location]).startswith(dropdir):
            responses.append({"filename": file.filename, "status": "failed", "error": "Invalid file path"})
            continue

        try:
            file_size = 0
            with open(file_location, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # Read in 1MB chunks
                    if not chunk:
                        break
                    file_size += len(chunk)

                    # Check file size incrementally
                    if file_size > max_upload_size_bytes:
                        os.remove(file_location)
                        raise Exception("File size exceeds limit")

                    # Check directory size incrementally
                    if current_directory_size + file_size > max_directory_size_bytes:
                        os.remove(file_location)
                        raise Exception("Directory size exceeds limit")

                    f.write(chunk)

            responses.append({"filename": file.filename, "status": "saved"})
            current_directory_size += file_size

        except Exception as e:
            responses.append({"filename": file.filename, "status": "failed", "error": str(e)})

    return {"files": responses}

@app.get("/api/config",
         summary="Show app configuration",
         description="Exposes app configuration relevant to the client, mostly so the client can enforce limits. These limits are also enforced serverside.",
         response_model=ServerStatusModel)
async def show_config():
    return {"maxUploadSize": settings.maxUploadSize}

# Serve static files from the 'www-static' directory at the web root
app.mount("/", StaticFiles(directory="www-static", html=True), name="static")

# To run the application, use the command: uvicorn shuttledrop:app --reload
