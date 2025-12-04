"""
Test script for Google Cloud Text-to-Speech with MultiSpeakerMarkup
Mimics the script generation step and converts to Google TTS format.

Setup:
1. Enable Cloud Text-to-Speech API in Google Cloud Console
2. Create a service account and download credentials.json
3. Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
   OR place credentials.json in the backend folder

Run from backend folder: python tests/test_google_tts.py
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.env_loader import load_backend_env
load_backend_env()


# ============================================================
# STEP 1: Sample Podcast Script (mimics script_agent.py output)
# ============================================================

SAMPLE_PODCAST_SCRIPT = {
    "title": "Agentic AI: The Next Frontier - December 2024",
    "sections": [
        {
            "type": "intro",
            "title": None,
            "dialog": [
                {"speaker": "ALEX", "text": "Welcome back to Tech Insights! I'm Alex."},
                {"speaker": "MORGAN", "text": "And I'm Morgan. Today we're diving into agentic AI."},
                {"speaker": "ALEX", "text": "This is one of the hottest topics in tech right now."},
                {"speaker": "MORGAN", "text": "Absolutely! Let's break it down for our listeners."},
            ]
        },
        {
            "type": "article",
            "title": "What is Agentic AI?",
            "dialog": [
                {"speaker": "ALEX", "text": "So Morgan, what exactly is agentic AI?"},
                {"speaker": "MORGAN", "text": "Great question! It's AI that can take autonomous actions."},
                {"speaker": "ALEX", "text": "You mean like making decisions on its own?"},
                {"speaker": "MORGAN", "text": "Exactly. It can plan, execute, and adapt without constant human input."},
                {"speaker": "ALEX", "text": "That's a big shift from traditional chatbots."},
                {"speaker": "MORGAN", "text": "Huge shift. We're talking about AI that can actually get things done."},
            ]
        },
        {
            "type": "outro",
            "title": None,
            "dialog": [
                {"speaker": "ALEX", "text": "Well, that's all the time we have for today."},
                {"speaker": "MORGAN", "text": "Thanks for listening everyone!"},
                {"speaker": "ALEX", "text": "See you next time on Tech Insights."},
                {"speaker": "MORGAN", "text": "Bye for now!"},
            ]
        }
    ],
    "sources": ["https://example.com/agentic-ai"]
}


# ============================================================
# STEP 2: Convert to Google Cloud TTS MultiSpeakerMarkup format
# ============================================================

def convert_script_to_multi_speaker_markup(script_data: dict) -> list:
    """
    Convert Gemini-generated podcast script to Google Cloud TTS turns format.
    
    Google MultiSpeakerMarkup supports speakers: R, S, T, U, V, W (up to 6)
    """
    # Map your speaker names to Google's speaker IDs
    speaker_map = {
        "ALEX": "R",    # First speaker (will use one voice)
        "MORGAN": "S",  # Second speaker (will use another voice)
    }
    
    turns = []
    
    # Flatten all sections' dialogs into one list
    for section in script_data.get("sections", []):
        for dialog in section.get("dialog", []):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            
            if text.strip():
                turns.append({
                    "text": text,
                    "speaker": speaker_map.get(speaker, "R")
                })
    
    return turns


def print_conversion_result(script_data: dict):
    """Print the conversion for verification"""
    print("\n" + "="*60)
    print("SCRIPT CONVERSION PREVIEW")
    print("="*60)
    
    turns = convert_script_to_multi_speaker_markup(script_data)
    
    print(f"\nTotal dialog turns: {len(turns)}")
    print(f"Total characters: {sum(len(t['text']) for t in turns)}")
    print("\nFirst 5 turns:")
    print("-"*40)
    
    for i, turn in enumerate(turns[:5]):
        speaker_name = "ALEX" if turn["speaker"] == "R" else "MORGAN"
        print(f"  [{turn['speaker']}] {speaker_name}: \"{turn['text'][:50]}...\"" if len(turn['text']) > 50 else f"  [{turn['speaker']}] {speaker_name}: \"{turn['text']}\"")
    
    if len(turns) > 5:
        print(f"  ... and {len(turns) - 5} more turns")
    
    return turns


# ============================================================
# STEP 3: Google Cloud TTS with MultiSpeakerMarkup
# ============================================================

def setup_google_credentials():
    """Setup Google Cloud credentials"""
    # Check for credentials in various locations
    cred_paths = [
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "google-credentials.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "service-account.json"),
    ]
    
    for path in cred_paths:
        if path and os.path.exists(path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
            print(f"✓ Found credentials at: {path}")
            return True
    
    print("\n⚠️  No credentials.json found!")
    print("\nTo setup Google Cloud TTS:")
    print("1. Go to: https://console.cloud.google.com/")
    print("2. Enable 'Cloud Text-to-Speech API'")
    print("3. Create a Service Account")
    print("4. Download the JSON key file")
    print("5. Save it as 'credentials.json' in the backend folder")
    print("   OR set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    return False


def generate_audio_google_tts(turns: list, output_path: str) -> bool:
    """
    Generate podcast audio using Google Cloud TTS MultiSpeakerMarkup
    Single API call for entire podcast!
    """
    try:
        from google.cloud import texttospeech
    except ImportError:
        print("\n❌ google-cloud-texttospeech not installed!")
        print("Run: pip install google-cloud-texttospeech")
        return False
    
    # Setup credentials
    if not setup_google_credentials():
        return False
    
    try:
        # Initialize client
        client = texttospeech.TextToSpeechClient()
        print("✓ Google Cloud TTS client initialized")
        
        # Convert turns to MultiSpeakerMarkup
        multi_speaker_markup = texttospeech.MultiSpeakerMarkup(
            turns=[
                texttospeech.MultiSpeakerMarkup.Turn(
                    text=turn["text"],
                    speaker=turn["speaker"]
                )
                for turn in turns
            ]
        )
        
        # Create synthesis input
        synthesis_input = texttospeech.SynthesisInput(
            multi_speaker_markup=multi_speaker_markup
        )
        
        # Configure voice (Studio MultiSpeaker for best quality)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Studio-MultiSpeaker"
        )
        
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        print("\n🔄 Generating podcast audio (single API call)...")
        print("   This may take 30-60 seconds for the full podcast...")
        
        # ONE API call for entire podcast!
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        
        file_size = os.path.getsize(output_path)
        print(f"\n✅ SUCCESS! Podcast audio generated!")
        print(f"   File: {output_path}")
        print(f"   Size: {file_size / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating audio: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# STEP 4: Run the test
# ============================================================

def main():
    print("="*60)
    print("Google Cloud TTS - MultiSpeakerMarkup Test")
    print("="*60)
    
    # Step 1: Show the sample script
    print("\n📝 STEP 1: Sample Podcast Script")
    print(f"   Title: {SAMPLE_PODCAST_SCRIPT['title']}")
    print(f"   Sections: {len(SAMPLE_PODCAST_SCRIPT['sections'])}")
    
    # Step 2: Convert to MultiSpeakerMarkup format
    print("\n🔄 STEP 2: Converting to Google TTS format...")
    turns = print_conversion_result(SAMPLE_PODCAST_SCRIPT)
    
    # Step 3: Generate audio
    print("\n🎙️ STEP 3: Generating Audio with Google Cloud TTS")
    output_path = os.path.join(os.path.dirname(__file__), "test_google_tts_output.mp3")
    
    success = generate_audio_google_tts(turns, output_path)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✅ TEST PASSED!")
        print(f"\n🎧 Play the audio file to hear the result:")
        print(f"   {output_path}")
        print("\n💰 Cost estimate:")
        total_chars = sum(len(t['text']) for t in turns)
        print(f"   Characters used: {total_chars}")
        print(f"   FREE tier remaining: {1_000_000 - total_chars:,} chars")
    else:
        print("❌ TEST FAILED")
        print("\nTroubleshooting:")
        print("1. Install: pip install google-cloud-texttospeech")
        print("2. Enable Cloud Text-to-Speech API in Google Cloud Console")
        print("3. Create service account and download credentials.json")
        print("4. Place credentials.json in backend folder")
    print("="*60)


if __name__ == "__main__":
    main()

