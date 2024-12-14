import os
import subprocess
from pathlib import Path
import tempfile
import ffmpeg
import re

class VideoDirCombinerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory_path": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Path to video directory"
                }),
                "output_filename": ("STRING", {
                    "default": "combined_output.mp4",
                    "multiline": False,
                    "placeholder": "output.mp4"
                }),
                "file_pattern": ("STRING", {
                    "default": "*.mp4",
                    "multiline": False,
                    "placeholder": "*.mp4"
                }),
                "transition": (["none", "fade"], {"default": "none"}),
                "transition_duration": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1,
                    "round": 0.1,
                }),
            },
            "optional": {
                "sort_files": ("BOOLEAN", {
                    "default": True,
                    "label": "Sort files alphabetically"
                }),
                "audio": ("AUDIO", {
                    "default": None,
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "combine_videos"
    CATEGORY = "video"
    OUTPUT_NODE = True

    def __init__(self):
        self.output_dir = self._get_output_directory()
        self.ffmpeg_path = "ffmpeg"  # Now using system ffmpeg

    @staticmethod
    def _get_output_directory():
        try:
            import folder_paths
            return folder_paths.get_output_directory()
        except ImportError:
            return os.getcwd()

    def _get_video_duration(self, video_path):
        """Get duration of video file using ffmpeg."""
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        return float(probe['format']['duration'])

    def combine_videos(self, directory_path: str, output_filename: str, 
                      file_pattern: str, transition: str = "none", 
                      transition_duration: float = 0.5,
                      sort_files: bool = True, 
                      audio: dict = None) -> tuple:
        """
        Combine all videos in the specified directory with optional audio and transitions.
        """
        # Verify inputs
        if not os.path.exists(directory_path):
            raise ValueError(f"Directory {directory_path} does not exist")
        
        # Get video files
        video_files = list(Path(directory_path).glob(file_pattern))
        if not video_files:
            raise ValueError(f"No video files matching {file_pattern} found in {directory_path}")
            
        if sort_files:
            video_files.sort()

        # Handle audio input
        audio_path = None
        if audio is not None and "audio_path" in audio:
            audio_path = audio["audio_path"]
            if not os.path.exists(audio_path):
                raise ValueError(f"Audio file {audio_path} does not exist")
        
        # Set output path
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            if transition == "none" or len(video_files) < 2:
                # Basic concatenation without transitions
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    for video_file in video_files:
                        f.write(f"file '{video_file.absolute()}'\n")
                    temp_list_path = f.name

                stream = ffmpeg.input(temp_list_path, f='concat', safe=0)
                
                if audio_path:
                    audio_stream = ffmpeg.input(audio_path)
                    stream = ffmpeg.output(stream, audio_stream, output_path,
                                        acodec='aac', vcodec='copy',
                                        shortest=None)
                else:
                    stream = ffmpeg.output(stream, output_path, c='copy')
                
            else:
                # Calculate durations for offset timing
                durations = [self._get_video_duration(str(v)) for v in video_files]
                total_duration = sum(durations) - (len(durations) - 1) * transition_duration
                
                # Build filter graph
                if len(video_files) == 2:
                    # Special case for two videos - simpler filter graph
                    input_1 = ffmpeg.input(str(video_files[0]))
                    input_2 = ffmpeg.input(str(video_files[1]))
                    
                    # Calculate precise offset
                    offset = durations[0] - transition_duration
                    
                    # Create crossfade
                    joined = ffmpeg.filter(
                        [input_1, input_2],
                        'xfade',
                        transition='fade',
                        duration=transition_duration,
                        offset=offset
                    )
                    
                    # Setup output
                    if audio_path:
                        audio_stream = ffmpeg.input(audio_path)
                        stream = ffmpeg.output(
                            joined,
                            audio_stream,
                            output_path,
                            acodec='aac'
                        )
                    else:
                        stream = ffmpeg.output(joined, output_path)
                else:
                    # For more than two videos
                    streams = [ffmpeg.input(str(v)) for v in video_files]
                    current = streams[0]
                    
                    # Chain crossfades
                    offset = 0
                    for i in range(1, len(streams)):
                        offset += durations[i-1] - transition_duration
                        current = ffmpeg.filter(
                            [current, streams[i]],
                            'xfade',
                            transition='fade',
                            duration=transition_duration,
                            offset=offset
                        )
                    
                    # Setup output
                    if audio_path:
                        audio_stream = ffmpeg.input(audio_path)
                        stream = ffmpeg.output(
                            current,
                            audio_stream,
                            output_path,
                            acodec='aac'
                        )
                    else:
                        stream = ffmpeg.output(current, output_path)

            # Print the ffmpeg command for debugging
            print("FFmpeg command:", ' '.join(stream.compile()))
            
            # Run the ffmpeg command
            stream.overwrite_output().run()
            
        except ffmpeg.Error as e:
            raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
            
        finally:
            if (transition == "none" or len(video_files) < 2) and 'temp_list_path' in locals():
                if os.path.exists(temp_list_path):
                    os.unlink(temp_list_path)
        
        return (output_path,)

# Register the node
NODE_CLASS_MAPPINGS = {
    "VideoDirCombiner": VideoDirCombinerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoDirCombiner": "Video Directory Combiner"
}