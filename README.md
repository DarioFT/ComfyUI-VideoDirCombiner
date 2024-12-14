# ComfyUI Video Directory Combiner

A custom node for ComfyUI that allows you to load and combine multiple videos from a directory automatically. Perfect for batch processing and combining multiple video segments into a single file.

## Features
- Load all videos from a specified directory
- Filter videos by file pattern (e.g., *.mp4, *.avi)
- Automatically combine videos using FFmpeg
- Preserves original video quality through stream copying
- Simple interface with just three parameters

## Installation

1. Make sure you have ComfyUI installed
2. Install FFmpeg if you haven't already
3. Clone this repository into your ComfyUI custom nodes directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/yourusername/comfyui-video-dir-combiner
```

## Requirements
- ComfyUI
- FFmpeg
- Python 3.x

## Usage

1. In ComfyUI, you'll find a new node called "Video Directory Combiner" under the "video" category
2. Connect the node and set:
   - directory_path: Path to your video files
   - output_filename: Desired name for combined video (default: combined_output.mp4)
   - file_pattern: Pattern to match video files (default: *.mp4)

## Example Workflow
![Example Workflow](examples/workflow.png)

## License
MIT License - See LICENSE file for details