# ComfyUI Video Directory Combiner

A custom node for ComfyUI that combines multiple videos from a directory with optional transitions and background music. Perfect for batch processing and creating seamless video compilations.

## Features

- Load and combine multiple videos from a specified directory
- Supports smooth transitions between video clips:
  - Fade transitions with configurable duration
  - Option to disable transitions for direct concatenation
- Audio support:
  - Add background music to your video compilation
  - Compatible with VideoHelperSuite's audio format
  - Audio automatically syncs with video duration
- Video handling options:
  - Filter videos by file pattern (e.g., *.mp4, *.avi)
  - Optional alphabetical sorting of video files
  - Preserves original video quality through stream copying when possible
- Clean interface with intuitive parameters
- Automatic temporary file cleanup

## Installation

1. Make sure you have ComfyUI installed
2. Install FFmpeg if you haven't already (and add it to you PATH)
3. Clone this repository into your ComfyUI custom nodes directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/DarioFT/ComfyUI-VideoDirCombiner
```

## Requirements

- ComfyUI
- FFmpeg
- Python 3.x
- Required Python packages:
  - ffmpeg-python

## Usage

In ComfyUI, you'll find a new node called "Video Directory Combiner" under the "video" category.

### Required Parameters:
- `directory_path`: Path to your folder containing the video files
- `output_filename`: Desired name for combined video (default: combined_output.mp4)
- `file_pattern`: Pattern to match video files (default: *.mp4)
- `transition`: Choose between "none" or "fade" (default: none)
- `transition_duration`: Duration of transitions in seconds (default: 0.5, range: 0.1-2.0)

### Optional Parameters:
- `sort_files`: Sort video files alphabetically (default: True)
- `music_track`: Audio input compatible with VideoHelperSuite's format

### Tips
- For smooth transitions, ensure your videos have similar resolutions and framerates
- When using music, the final video will end when either the video compilation or music ends (whichever is shorter)
- Sort your files alphabetically for predictable ordering of video clips
- Use meaningful filenames if you need specific video ordering

## Integration with VideoHelperSuite

This node works seamlessly with VideoHelperSuite's audio functionality:
1. Use VideoHelperSuite's LoadVideo node to load your audio file
2. Connect the LoadVideo node's audio output to VideoDirCombiner's music_track input
3. The audio will be automatically synchronized with your video compilation

## Troubleshooting

Common issues and solutions:

- **FFmpeg not found**: Ensure FFmpeg is installed and accessible in your system PATH
- **Video quality issues**: Check if all input videos use compatible codecs and settings
- **No audio**: Verify that the audio input is properly connected and the audio file exists
- **Transition glitches**: Ensure videos have similar framerates and formats

## License

MIT License - See LICENSE file for details