import websocket 
import uuid
import json
import urllib.request
import urllib.parse
import random
import os
import requests

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())

workflow_file = "image-to-image-workflow.json"
input_image = "input/man-smoking.png"
checkpoint_model = "juggernautXL_juggXIByRundiffusion.safetensors"
positive_prompt = "portrait photo of a bolded and bearded man smoking a cigar, wearing glasses, 35 years old" 

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break #Execution is done
        else:
            # If you want to be able to decode the binary stream for latent previews, here is how you can do it:
            # bytesIO = BytesIO(out[8:])
            # preview_image = Image.open(bytesIO) # This is your preview in PIL image format, store it in a global
            continue #previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images

def upload_file(file, subfolder="", overwrite=False):
    try:
        body = {"image": file}
        data = {}
        
        if overwrite:
            data["overwrite"] = "true"
  
        if subfolder:
            data["subfolder"] = subfolder

        resp = requests.post(f"http://{server_address}/upload/image", files=body,data=data)
        
        if resp.status_code == 200:
            data = resp.json()
            path = data["name"]
            if "subfolder" in data:
                if data["subfolder"] != "":
                    path = data["subfolder"] + "/" + path
        else:
            print(f"{resp.status_code} - {resp.reason}")
    except Exception as error:
        print(error)
    return path


# upload an image
with open(input_image, "rb") as f:
    comfyui_upload_image_path = upload_file(f,"",True)

# load workflow
with open(workflow_file, "r", encoding="utf-8") as wf_json:
    workflow = wf_json.read()


prompt = json.loads(workflow)

# set checkpoint model
prompt["1"]["inputs"]["ckpt_name"] = checkpoint_model

# set the input image
prompt["2"]["inputs"]["image"] = comfyui_upload_image_path

# set positive prompt
prompt["4"]["inputs"]["text"] = positive_prompt

# set the seed 
seed = random.randint(100000, 999999)
prompt["3"]["inputs"]["seed"] = seed


print(f"Running workflow: {workflow_file}")
print(f"- with input image: {input_image}")
print(f"- with model: {checkpoint_model}")
print(f"- with seed: {seed}")
print(f"- with prompt: {positive_prompt}\n")

ws = websocket.WebSocket()
ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
images = get_images(ws, prompt)
ws.close() 

# write generated image into result folder 
outout_folder_name = "output"
os.makedirs(outout_folder_name, exist_ok=True)


for node_id in images:
    for image_data in images[node_id]:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_data))
        result_image = f"{outout_folder_name}/image_{seed}.png" 
        image.save(result_image, format="PNG")
        print(f"Result image saved: {result_image}")
        # image.show()

