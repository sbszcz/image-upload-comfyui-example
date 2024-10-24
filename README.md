# ComfyUI API Usage Example

Requirements:

- python v3.12 and above
- running ComfyUI instance (example defaults to: http://127.0.0.1:8188)
- Checkpoint Model: [Juggernaut XL](https://civitai.com/models/133005/juggernaut-xl)

## What does the script do?

This little script uploads an input image (see `input` folder) via http API, starts the workflow (see: `image-to-image-workflow.json`) and generates images described by the input prompt.
All generates images are saved in the output folder containing the random seed as part of the filename (e.g. `output/image_123456.png`)

## How to run

```bash
git clone https://github.com/sbszcz/image-upload-comfyui-example.git
cd image-upload-comfyui-example
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run-workflow.py
```

## How to configure

Adjust the top variables inside the script file `run-workflow.py`.

For example: `workflow_file`, `input_image`, `checkpoint_model`, `positive_prompt`
