from agno.agent import Agent
import os
from datetime import datetime
import tempfile
import numpy as np
import soundfile as sf
from typing import Any, Dict, List, Optional, Tuple
from utils.load_api_keys import load_api_key
from utils.text_to_audio_elevenslab import create_podcast as create_podcast_elevenlabs
from openai import OpenAI
from scipy import signal


PODCASTS_FOLDER = "podcasts"
PODCAST_AUDIO_FOLDER = os.path.join(PODCASTS_FOLDER, "audio")
PODCAST_MUSIC_FOLDER = os.path.join('static', "musics")
OPENAI_VOICES = {1: "alloy", 2: "echo", 3: "fable", 4: "onyx", 5: "nova", 6: "shimmer"}
DEFAULT_VOICE_MAP = {1: "alloy", 2: "nova"}
ELEVENLABS_VOICE_MAP = {1: "Rachel", 2: "Adam"}
# Edge TTS voices - high quality, FREE, unlimited
EDGE_TTS_VOICE_MAP = {
    1: "en-US-GuyNeural",      # Alex (male, natural)
    2: "en-US-JennyNeural"     # Morgan (female, natural)
}
TTS_MODEL = "gpt-4o-mini-tts"
INTRO_MUSIC_FILE = os.path.join(PODCAST_MUSIC_FOLDER, "intro_audio.mp3")
OUTRO_MUSIC_FILE = os.path.join(PODCAST_MUSIC_FOLDER, "intro_audio.mp3")


def resample_audio_scipy(audio, original_sr, target_sr):
    if original_sr == target_sr:
        return audio
    resampling_ratio = target_sr / original_sr
    num_samples = int(len(audio) * resampling_ratio)
    resampled = signal.resample(audio, num_samples)
    return resampled


async def create_podcast_edge_tts_parallel(
    script_entries: List[Dict],
    output_path: str,
    voice_map: Dict[int, str] = None,
) -> Optional[str]:
    """
    Generate podcast audio using Edge TTS with PARALLEL processing.
    FREE, unlimited, and 2x faster than sequential!
    
    Args:
        script_entries: List of {"text": str, "speaker": int} dicts
        output_path: Path to save the final audio file
        voice_map: Map of speaker_id to Edge TTS voice name
    
    Returns:
        Path to generated audio file, or None on failure
    """
    import time
    import shutil
    start_time = time.time()
    
    # CRITICAL: Configure FFmpeg BEFORE importing pydub!
    # Pydub checks for ffmpeg at import time and caches the result.
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not ffmpeg_path:
        # WinGet installs FFmpeg here
        winget_packages = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages")
        if os.path.exists(winget_packages):
            for folder in os.listdir(winget_packages):
                if "FFmpeg" in folder:
                    bin_path = os.path.join(winget_packages, folder)
                    # Find the bin folder with ffmpeg.exe
                    for root, dirs, files in os.walk(bin_path):
                        if "ffmpeg.exe" in files:
                            ffmpeg_path = os.path.join(root, "ffmpeg.exe")
                            break
                    if ffmpeg_path:
                        break
    
    if not ffmpeg_path:
        print("❌ FFmpeg not found! Install: winget install FFmpeg", flush=True)
        return None
    
    # Add FFmpeg to PATH BEFORE importing pydub
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    current_path = os.environ.get("PATH", "")
    if ffmpeg_dir not in current_path:
        os.environ["PATH"] = f"{ffmpeg_dir};{current_path}"
        print(f"✅ Added FFmpeg to PATH: {ffmpeg_dir}", flush=True)
    
    # NOW import pydub (after FFmpeg is in PATH)
    try:
        import edge_tts
        import asyncio
        from pydub import AudioSegment
    except ImportError as e:
        print(f"Edge TTS dependencies missing: {e}. Install with: pip install edge-tts pydub", flush=True)
        return None
    
    # Configure pydub with explicit paths
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffprobe = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe")
    print(f"✅ FFmpeg configured: {ffmpeg_path}", flush=True)
    
    voice_map = voice_map or EDGE_TTS_VOICE_MAP
    
    print(f"🎙️ Starting Edge TTS PARALLEL generation for {len(script_entries)} segments...", flush=True)
    
    # Create temp directory for individual segments
    temp_dir = tempfile.mkdtemp(prefix="edge_tts_")
    print(f"📁 Temp directory: {temp_dir}", flush=True)
    temp_files = []
    
    async def generate_segment(entry: Dict, index: int) -> Optional[str]:
        """Generate a single TTS segment using stream() for reliability."""
        text = entry.get("text", "").strip()
        speaker_id = entry.get("speaker", 1)
        
        if not text:
            return None
        
        voice = voice_map.get(speaker_id, "en-US-GuyNeural")
        temp_file = os.path.join(temp_dir, f"segment_{index:04d}.mp3")
        
        try:
            communicate = edge_tts.Communicate(text, voice)
            
            # Use stream() instead of save() for more reliable file writing
            with open(temp_file, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
            
            # Verify file was actually created
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                return temp_file
            else:
                print(f"  ✗ Segment {index}: File empty or not created", flush=True)
                return None
        except Exception as e:
            print(f"  ✗ Segment {index} failed: {e}", flush=True)
            return None
    
    try:
        # Generate all segments in PARALLEL
        tasks = [generate_segment(entry, i) for i, entry in enumerate(script_entries)]
        temp_files = await asyncio.gather(*tasks)
        
        tts_time = time.time() - start_time
        success_count = sum(1 for f in temp_files if f)
        print(f"✅ TTS generation complete: {success_count}/{len(script_entries)} in {tts_time:.1f}s", flush=True)
        
        # Debug: Check what's actually in the temp directory
        if os.path.exists(temp_dir):
            actual_files = os.listdir(temp_dir)
            print(f"📁 Temp dir contains {len(actual_files)} files: {actual_files[:5]}...", flush=True)
        else:
            print(f"❌ Temp directory doesn't exist: {temp_dir}", flush=True)
        
        # Combine audio segments (must be sequential to maintain order)
        print("🔗 Combining audio segments...", flush=True)
        combine_start = time.time()
        
        # CRITICAL: Re-verify FFmpeg is configured for pydub before combining
        print(f"🔧 Verifying pydub FFmpeg config:", flush=True)
        print(f"   AudioSegment.converter = {AudioSegment.converter}", flush=True)
        print(f"   AudioSegment.ffprobe = {AudioSegment.ffprobe}", flush=True)
        
        # Double-check first file exists
        if temp_files and temp_files[0]:
            test_file = temp_files[0]
            print(f"🔍 Testing first file: {test_file}", flush=True)
            print(f"   Exists: {os.path.exists(test_file)}", flush=True)
            if os.path.exists(test_file):
                print(f"   Size: {os.path.getsize(test_file)} bytes", flush=True)
                
                # Direct FFmpeg test
                import subprocess
                try:
                    result = subprocess.run(
                        [ffmpeg_path, "-version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    print(f"   FFmpeg runs: {result.returncode == 0}", flush=True)
                except Exception as ffmpeg_err:
                    print(f"   FFmpeg test failed: {ffmpeg_err}", flush=True)
        
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=500)  # 500ms pause between segments
        
        for i, temp_file in enumerate(temp_files):
            if temp_file and os.path.exists(temp_file):
                try:
                    segment = AudioSegment.from_mp3(temp_file)
                    if len(combined) > 0:
                        combined += silence
                    combined += segment
                except Exception as e:
                    print(f"  ⚠️ Could not load segment {i}: {e}", flush=True)
        
        if len(combined) == 0:
            print("❌ No audio segments could be combined", flush=True)
            return None
        
        # Export final audio
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        combined.export(output_path, format="mp3")
        
        total_time = time.time() - start_time
        duration_mins = len(combined) / 1000 / 60
        
        print(f"✅ Audio saved: {output_path}", flush=True)
        print(f"📊 Stats: {duration_mins:.1f} min podcast generated in {total_time:.1f}s (FREE!)", flush=True)
        
        return output_path
        
    finally:
        # Cleanup temp files
        import shutil
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def create_podcast_edge_tts(script_entries: List[Dict], output_path: str, voice_map: Dict[int, str] = None) -> Optional[str]:
    """Synchronous wrapper for Edge TTS parallel generation."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        pass
    
    return asyncio.run(create_podcast_edge_tts_parallel(script_entries, output_path, voice_map))


def create_silence_audio(silence_duration: float, sampling_rate: int) -> np.ndarray:
    if sampling_rate <= 0:
        print(f"Invalid sampling rate ({sampling_rate}) for silence generation")
        return np.zeros(0, dtype=np.float32)
    return np.zeros(int(sampling_rate * silence_duration), dtype=np.float32)


def combine_audio_segments(audio_segments: List[np.ndarray], silence_duration: float, sampling_rate: int) -> np.ndarray:
    if not audio_segments:
        return np.zeros(0, dtype=np.float32)
    silence = create_silence_audio(silence_duration, sampling_rate)
    combined_segments = []
    for i, segment in enumerate(audio_segments):
        combined_segments.append(segment)
        if i < len(audio_segments) - 1:
            combined_segments.append(silence)
    combined = np.concatenate(combined_segments)
    max_amp = np.max(np.abs(combined))
    if max_amp > 0:
        combined = combined / max_amp * 0.95
    return combined


def process_audio_file(temp_path: str) -> Optional[Tuple[np.ndarray, int]]:
    try:
        from pydub import AudioSegment

        audio_segment = AudioSegment.from_mp3(temp_path)
        channels = audio_segment.channels
        sample_width = audio_segment.sample_width
        frame_rate = audio_segment.frame_rate
        samples = np.array(audio_segment.get_array_of_samples())
        if channels == 2:
            samples = samples.reshape(-1, 2).mean(axis=1)
        max_possible_value = float(2 ** (8 * sample_width - 1))
        samples = samples.astype(np.float32) / max_possible_value
        return samples, frame_rate
    except ImportError:
        print("Pydub not available, falling back to soundfile")
    except Exception as e:
        print(f"Pydub processing failed: {e}")
    try:
        audio_np, samplerate = sf.read(temp_path)
        return audio_np, samplerate
    except Exception as e:
        print(f"Failed to process audio with soundfile: {e}")
        try:
            from pydub import AudioSegment

            sound = AudioSegment.from_mp3(temp_path)
            wav_path = temp_path.replace(".mp3", ".wav")
            sound.export(wav_path, format="wav")
            audio_np, samplerate = sf.read(wav_path)
            os.unlink(wav_path)
            return audio_np, samplerate
        except Exception as e:
            print(f"All audio processing methods failed: {e}")
    return None


def resample_audio(audio, orig_sr, target_sr):
    try:
        import librosa

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        print("Librosa not available for resampling")
        return audio
    except Exception as e:
        print(f"Resampling failed: {e}")
        return audio


def text_to_speech_openai(
    client: OpenAI,
    text: str,
    speaker_id: int,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        print("Empty text provided, skipping TTS generation")
        return None
    voice_map = voice_map or DEFAULT_VOICE_MAP
    voice = voice_map.get(speaker_id)
    if not voice:
        if speaker_id in OPENAI_VOICES:
            voice = OPENAI_VOICES[speaker_id]
        else:
            voice = next(iter(voice_map.values()), "alloy")
        print(f"No voice mapping for speaker {speaker_id}, using {voice}")
    try:
        print(f"Generating TTS for speaker {speaker_id} using voice '{voice}'")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        audio_data = response.content
        if not audio_data:
            print("OpenAI TTS returned empty response")
            return None
        print(f"Received {len(audio_data)} bytes from OpenAI TTS")
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        try:
            return process_audio_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"OpenAI TTS API error: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_podcast(
    script: Any,
    output_path: str,
    tts_engine: str = "openai",
    language_code: str = "en",
    silence_duration: float = 0.7,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[str]:
    if tts_engine.lower() != "openai":
        print(f"Only OpenAI TTS engine is available in this standalone version. Requested: {tts_engine}")
        return None
    try:
        api_key = load_api_key("OPENAI_API_KEY")
        if not api_key:
            print("No OpenAI API key provided")
            return None
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if voice_map is None:
        voice_map = DEFAULT_VOICE_MAP.copy()
    model_to_use = model
    if model == "tts-1" and language_code == "en":
        model_to_use = "tts-1-hd"
        print(f"Using high-definition TTS model for English: {model_to_use}")
    generated_segments = []
    sampling_rate_detected = None

    if hasattr(script, "entries"):
        entries = script.entries
    else:
        entries = script

    print(f"Processing {len(entries)} script entries", flush=True)
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        print(f"Processing entry {i + 1}/{len(entries)}: Speaker {speaker_id}", flush=True)
        result = text_to_speech_openai(
            client=client,
            text=entry_text,
            speaker_id=speaker_id,
            voice_map=voice_map,
            model=model_to_use,
        )
        if result:
            segment_audio, segment_rate = result
            if sampling_rate_detected is None:
                sampling_rate_detected = segment_rate
                print(f"Using sample rate: {sampling_rate_detected} Hz")
            elif sampling_rate_detected != segment_rate:
                print(f"Sample rate mismatch: {sampling_rate_detected} vs {segment_rate}")
                try:
                    segment_audio = resample_audio(segment_audio, segment_rate, sampling_rate_detected)
                    print(f"Resampled to {sampling_rate_detected} Hz")
                except Exception as e:
                    sampling_rate_detected = segment_rate
                    print(f"Resampling failed: {e}")
            generated_segments.append(segment_audio)
        else:
            print(f"Failed to generate audio for entry {i + 1}")
    if not generated_segments:
        print("No audio segments were generated")
        return None
    if sampling_rate_detected is None:
        print("Could not determine sample rate")
        return None
    print(f"Combining {len(generated_segments)} audio segments", flush=True)
    full_audio = combine_audio_segments(generated_segments, silence_duration, sampling_rate_detected)
    if full_audio.size == 0:
        print("Combined audio is empty")
        return None

    try:
        if os.path.exists(INTRO_MUSIC_FILE):
            intro_music, intro_sr = sf.read(INTRO_MUSIC_FILE)
            print(f"Loaded intro music: {len(intro_music) / intro_sr:.1f} seconds")

            if intro_music.ndim == 2:
                intro_music = np.mean(intro_music, axis=1)

            if intro_sr != sampling_rate_detected:
                intro_music = resample_audio_scipy(intro_music, intro_sr, sampling_rate_detected)

            full_audio = np.concatenate([intro_music, full_audio])
            print("Added intro music")

        if os.path.exists(OUTRO_MUSIC_FILE):
            outro_music, outro_sr = sf.read(OUTRO_MUSIC_FILE)
            print(f"Loaded outro music: {len(outro_music) / outro_sr:.1f} seconds")

            if outro_music.ndim == 2:
                outro_music = np.mean(outro_music, axis=1)

            if outro_sr != sampling_rate_detected:
                outro_music = resample_audio_scipy(outro_music, outro_sr, sampling_rate_detected)

            full_audio = np.concatenate([full_audio, outro_music])
            print("Added outro music")

    except Exception as e:
        print(f"Could not add intro/outro music: {e}")
        print("Continuing without background music")

    print(f"Writing audio to {output_path}", flush=True)
    try:
        sf.write(output_path, full_audio, sampling_rate_detected)
    except Exception as e:
        print(f"Failed to write audio file: {e}")
        return None
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"Audio file created: {output_path} ({file_size / 1024:.1f} KB)")
        return output_path
    else:
        print(f"Failed to create audio file at {output_path}")
        return None


def audio_generate_agent_run(agent: Agent) -> str:
    """
    Generate an audio file for the podcast using the selected TTS engine.

    Args:
        agent: The agent instance

    Returns:
        A message with the result of audio generation
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    
    script_data = session_state.get("generated_script", {})
    if not script_data or (isinstance(script_data, dict) and not script_data.get("sections")):
        error_msg = "Cannot generate audio: No podcast script data found. Please generate a script first."
        print(error_msg)
        return error_msg
    if isinstance(script_data, dict):
        podcast_title = script_data.get("title", "Your Podcast")
    else:
        podcast_title = "Your Podcast"
    session_state["stage"] = "audio"
    audio_dir = PODCAST_AUDIO_FOLDER
    audio_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_path = os.path.join(audio_dir, audio_filename)
    try:
        if isinstance(script_data, dict) and "sections" in script_data:
            speaker_map = {"ALEX": 1, "MORGAN": 2}
            script_entries = []
            for section in script_data.get("sections", []):
                for dialog in section.get("dialog", []):
                    speaker = dialog.get("speaker", "ALEX")
                    text = dialog.get("text", "")

                    if text and speaker in speaker_map:
                        script_entries.append({"text": text, "speaker": speaker_map[speaker]})
            if not script_entries:
                error_msg = "Cannot generate audio: No dialog found in the script."
                print(error_msg)
                return error_msg

            selected_language = session_state.get("selected_language", {"code": "en", "name": "English"})
            language_code = selected_language.get("code", "en")
            language_name = selected_language.get("name", "English")

            # TTS Engine Priority: edge (free+fast) > elevenlabs > openai
            preferred_engine = session_state.get("tts_engine")
            elevenlabs_api_key = load_api_key("ELEVENLABS_API_KEY")
            openai_api_key = load_api_key("OPENAI_API_KEY")
            
            # Check if edge-tts is available
            edge_tts_available = False
            try:
                import edge_tts
                edge_tts_available = True
            except ImportError:
                pass
            
            if preferred_engine:
                tts_engine = preferred_engine.lower()
            elif edge_tts_available:
                # Edge TTS is FREE and FAST - use it by default!
                tts_engine = "edge"
            elif elevenlabs_api_key:
                tts_engine = "elevenlabs"
            elif openai_api_key:
                tts_engine = "openai"
            else:
                # Fallback to edge even if not explicitly available
                tts_engine = "edge"

            # Validate engine availability
            if tts_engine == "elevenlabs" and not elevenlabs_api_key:
                print("ELEVENLABS_API_KEY not found. Falling back to Edge TTS.", flush=True)
                tts_engine = "edge"

            if tts_engine == "openai" and not openai_api_key:
                print("OPENAI_API_KEY not found. Falling back to Edge TTS.", flush=True)
                tts_engine = "edge"

            print(f"🎙️ Generating podcast audio using {tts_engine.upper()} TTS engine in {language_name} language", flush=True)
            
            # Change output to .mp3 for Edge TTS
            if tts_engine == "edge":
                audio_path = audio_path.replace(".wav", ".mp3")
            
            if tts_engine == "edge":
                # Edge TTS - FREE, unlimited, parallel (2x faster!)
                full_audio_path = create_podcast_edge_tts(
                    script_entries=script_entries,
                    output_path=audio_path,
                    voice_map=EDGE_TTS_VOICE_MAP,
                )
            elif tts_engine == "elevenlabs":
                full_audio_path = create_podcast_elevenlabs(
                    script=script_entries,
                    output_path=audio_path,
                    lang_code=language_code,
                    voice_map=ELEVENLABS_VOICE_MAP,
                    api_key=elevenlabs_api_key,
                )
            else:
                full_audio_path = create_podcast(
                    script=script_entries,
                    output_path=audio_path,
                    tts_engine="openai",
                    language_code=language_code,
                )
            if not full_audio_path:
                error_msg = f"Failed to generate podcast audio with {tts_engine} TTS engine."
                print(error_msg)
                return error_msg

            audio_url = f"{os.path.basename(full_audio_path)}"
            session_state["audio_url"] = audio_url
            session_state["show_audio_for_confirmation"] = True
            SessionService.save_session(session_id, session_state)
            print(f"✅ Successfully generated podcast audio: {full_audio_path}", flush=True)
            
            engine_label = "Edge TTS (Free)" if tts_engine == "edge" else tts_engine.capitalize()
            return f"I have completed your podcast on '{podcast_title}'. The audio has been generated using {engine_label} voices in {language_name}. You can listen to it in the player below. If it sounds good, click 'Sounds Great!' to complete your podcast."
        else:
            error_msg = "Cannot generate audio: Script is not in the expected format."
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error generating podcast audio: {str(e)}"
        print(error_msg, flush=True)
        return f"I encountered an error while generating the podcast audio: {str(e)}. Please try again or let me know if you'd like to proceed without audio."