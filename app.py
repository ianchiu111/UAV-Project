# app.py
import os
import random
import tempfile
import base64
import requests

from flask import Flask, request, render_template
from GPT_Model import model_response, base64_response

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    # 1) Check if single file was uploaded
    single_file = request.files.get("single_file")
    
    # 2) Check if folder was uploaded
    folder_files = request.files.getlist("folder")

    # 3) Also get the 'n' field for random selection
    n_str = request.form.get("n", "1")
    try:
        n = int(n_str)
    except ValueError:
        n = 1
    
    # If the user provided a single file
    if single_file and single_file.filename:
        # Handle single file logic, e.g.:
        #   - read file, base64-encode it, pass to GPT
        image_data = single_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
        
        reply = model_response(base64_image)
        return f"<pre>Single file uploaded:\n{reply}</pre>"
    
    # If the user provided a folder
    elif folder_files and len(folder_files) > 0 and folder_files[0].filename:
        # We'll have multiple files. Let's store them temporarily, filter out non-images, etc.
        temp_dir = tempfile.mkdtemp(prefix="uploaded_")
        image_paths = []
        allowed_ext = {".jpg", ".jpeg", ".png"}
        
        for file_obj in folder_files:
            filename = file_obj.filename
            _, ext = os.path.splitext(filename.lower())
            if ext in allowed_ext:
                save_path = os.path.join(temp_dir, os.path.basename(filename))
                file_obj.save(save_path)
                image_paths.append(save_path)
        
        if not image_paths:
            return "<pre>No valid images found in the uploaded folder.</pre>"
        
        # Randomly pick N from the uploaded images
        if len(image_paths) <= n:
            selected_paths = image_paths
        else:
            selected_paths = random.sample(image_paths, n)
        
        results = []
        for path in selected_paths:
            with open(path, "rb") as f:
                base64_image = base64.b64encode(f.read()).decode("utf-8")
            gpt_reply = model_response(base64_image)
            results.append(f"File: {os.path.basename(path)}\nGPT Reply:\n{gpt_reply}\n" + "-"*40)
        
        return f"<pre>{'\n\n'.join(results)}</pre>"
    
    else:
        # If neither single file nor folder was uploaded, show an error
        return "<pre>No file or folder selected.</pre>"



@app.route("/upload_folder", methods=["GET", "POST"])
def upload_folder():
    if request.method == "GET":
        # Render the form (upload_folder.html)
        return render_template("upload_folder.html")

    # If POST:
    # 1. Get all files from request.files
    files = request.files.getlist("folder")
    n_str = request.form.get("n", "1")
    try:
        n = int(n_str)
    except ValueError:
        n = 1

    # 2. Filter out non-image files & store them to a temp folder
    #    We'll store them in a local tmp folder (or in memory).
    #    Make sure you have "import tempfile"
    temp_dir = tempfile.mkdtemp(prefix="uploaded_")
    
    image_paths = []
    allowed_ext = {".jpg", ".jpeg", ".png"}

    for file_obj in files:
        filename = file_obj.filename  # e.g. subfolder/img1.jpg
        _, ext = os.path.splitext(filename.lower())
        if ext in allowed_ext:
            # Save this file in our temporary directory
            save_path = os.path.join(temp_dir, os.path.basename(filename))
            file_obj.save(save_path)
            image_paths.append(save_path)

    if not image_paths:
        return "<pre>No valid .jpg/.jpeg/.png files found in the uploaded folder.</pre>"

    # 3. Randomly select N images from what the user uploaded
    if len(image_paths) <= n:
        selected_paths = image_paths
    else:
        selected_paths = random.sample(image_paths, n)

    # 4. For each selected image, convert to base64 and pass to the GPT model
    results = []
    for path in selected_paths:
        with open(path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        # call your GPT-based function (model_response, etc.)
        gpt_reply = model_response(base64_image)
        # store the results
        result_str = (
            f"Randomly Picked: {path}\n"
            f"GPT Model Reply:\n{gpt_reply}\n"
            + ("-" * 50)
        )
        results.append(result_str)

    # 5. Return results as text (or render a new template)
    combined_output = "\n\n".join(results)
    return f"<pre>{combined_output}</pre>"


@app.route("/random", methods=["GET", "POST"])
def random_images():
    """
    範例：保留你原本的隨機抽取圖片功能
    """
    if request.method == "POST":
        path = request.form.get("path", "")
        n_str = request.form.get("n", "1")
        try:
            n = int(n_str)
        except ValueError:
            n = 1

        try:
            results = base64_response(path, n)
            return f"<pre>{results}</pre>"
        except Exception as e:
            return f"<pre>Error: {e}</pre>"

    return render_template("random.html")


if __name__ == "__main__":
    app.run(debug=True)
