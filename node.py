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
                "music_track": ("AUDIO",),  # VideoHelperSuite audio format
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "combine_videos"
    CATEGORY = "video"
    OUTPUT_NODE = True

    def __init__(self):
        self.output_dir = self._get_output_directory()
        self.ffmpeg_path = "ffmpeg"

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

    def _process_vhs_audio(self, audio_dict):
        """Process VideoHelperSuite audio format."""
        if not audio_dict or 'waveform' not in audio_dict or 'sample_rate' not in audio_dict:
            return None, None

        # Create a temporary file for the audio
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        try:
            # Convert waveform to raw PCM data
            channels = audio_dict['waveform'].size(1)
            audio_data = audio_dict['waveform'].squeeze(0).transpose(0, 1).numpy().tobytes()
            
            # Use ffmpeg to create a WAV file
            args = [
                self.ffmpeg_path,
                '-y',  # Overwrite output file if it exists
                '-f', 'f32le',  # Input format (32-bit float PCM)
                '-ar', str(audio_dict['sample_rate']),  # Sample rate
                '-ac', str(channels),  # Number of channels
                '-i', '-',  # Read from stdin
                '-acodec', 'pcm_s16le',  # Output codec
                temp_audio.name
            ]
            
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=audio_data)
            
            if process.returncode != 0:
                print(f"Warning: Failed to process audio: {stderr.decode()}")
                return None, None
            
            return temp_audio.name, temp_audio
            
        except Exception as e:
            print(f"Warning: Error processing audio: {str(e)}")
            return None, None

    def combine_videos(self, directory_path: str, output_filename: str, 
                      file_pattern: str, transition: str = "none", 
                      transition_duration: float = 0.5,
                      sort_files: bool = True, 
                      music_track: dict = None) -> tuple:
        """
        Combine all videos in the specified directory and add a music track.
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

        # Process VHS audio format
        audio_path = None
        temp_audio = None
        
        if music_track is not None:
            audio_path, temp_audio = self._process_vhs_audio(music_track)
        
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
                    output_args = {
                        'acodec': 'aac',
                        'vcodec': 'copy',
                    }
                    # Pass shortest as a flag without value
                    stream = ffmpeg.output(
                        stream,
                        audio_stream,
                        output_path,
                        **output_args,
                        shortest=None  # This makes it a flag without value
                    )
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
                    
                    # Setup output with audio
                    if audio_path:
                        audio_stream = ffmpeg.input(audio_path)
                        output_args = {
                            'acodec': 'aac',
                        }
                        stream = ffmpeg.output(
                            joined,
                            audio_stream,
                            output_path,
                            **output_args,
                            shortest=None  # This makes it a flag without value
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
                    
                    # Setup output with audio
                    if audio_path:
                        audio_stream = ffmpeg.input(audio_path)
                        output_args = {
                            'acodec': 'aac',
                        }
                        stream = ffmpeg.output(
                            current,
                            audio_stream,
                            output_path,
                            **output_args,
                            shortest=None  # This makes it a flag without value
                        )
                    else:
                        stream = ffmpeg.output(current, output_path)

            # Print the ffmpeg command for debugging
            print("FFmpeg command:", ' '.join(stream.compile()))
            
            # Run the ffmpeg command
            stream.overwrite_output().run()
            
        except ffmpeg.Error as e:
            if e.stderr is not None:
                raise RuntimeError(f"FFmpeg error: {e.stderr.decode()}")
            else:
                raise RuntimeError(f"FFmpeg error: {str(e)}")
            
        finally:
            # Clean up temporary files
            if (transition == "none" or len(video_files) < 2) and 'temp_list_path' in locals():
                if os.path.exists(temp_list_path):
                    os.unlink(temp_list_path)
            if temp_audio is not None:
                temp_audio.close()
                if os.path.exists(temp_audio.name):
                    os.unlink(temp_audio.name)
        
        return (output_path,)

# Register the node
NODE_CLASS_MAPPINGS = {
    "VideoDirCombiner": VideoDirCombinerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoDirCombiner": "Video Directory Combiner"
}