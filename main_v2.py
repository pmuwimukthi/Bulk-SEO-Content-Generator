import streamlit as st
import os
from pathlib import Path
from groq import Groq
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Podcast Transcription & SEO Generator",
    page_icon="🎙️",
    layout="wide"
)

# Initialize session state
if 'transcriptions' not in st.session_state:
    st.session_state.transcriptions = {}
if 'formatted_output' not in st.session_state:
    st.session_state.formatted_output = ""
if 'file_location' not in st.session_state:
    st.session_state.file_location = ""

# Get API key from environment
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Check if API key exists
if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY not found in .env file. Please add your API key to the .env file.")
    st.stop()

# Hardcoded podcast data
PODCAST_DATA = {
    "orenda": "this is Shattering Inequities Podcast the host is Dr. Robin Avelar-La Salle",
    "first line": "Interviews with world-class performers from various areas to extract tactics and tools",
    "ETMA": "Stories behind some of the world's best known companies and the innovators who built them",
    "cloud 113": "Science tackles fads, trends, and the opinionated mob to find out what's fact, what's not",
    "clean connect": "this is Empirical Energy Podcast the host is Mark smith",
    "Reply All": "A show about the internet and modern life, hosted by PJ Vogt and Alex Goldman",
    "Radiolab": "Investigative journalism meets radio theater with big questions and ideas",
    "This American Life": "Weekly public radio show and podcast, mostly journalistic non-fiction stories"
}

# Default instruction prompt
DEFAULT_INSTRUCTION_PROMPT = """General Instructions:

You are a professional SEO content generator for podcasts.
Generate SEO-optimized titles, detailed descriptions, and relevant tags. We expect long and detailed descriptions for each video, especially the full video. Tags should be comma-separated.
If transcription is not available, don't write anything for that video.

Title for full podcast:
Description for full podcast:
Tags for full podcast (a list separated by commas):

Additional instructions:
- Title should be in this format: short title | guest name | podcast name | ep no
- Format the description as follows:
  * Short description
  * Tune in inside (small list of keywords of main topics discussed in the podcast)
  * Key takeaways (in bullet point format)
  * Add chapters using exact times from full transcription in regular YouTube chapters format
  * Quote of the show (one sentence with exact words from the guest)
  * Hashtags at the very end (#hashtag1 #hashtag2 #hashtag3)
  * Call to action (subscribe, like, etc.) as a sentence at the end

Title for trailer video:
Description for trailer video:
Tags for trailer video (a list separated by commas):

Requirements:
- Use "|" instead of "+" in titles
- At least 400+ words for full episode description
- At least 300+ words for each other video description
- Don't use markdown format in descriptions and titles
- Don't name sections like "Call to Action" - just write them naturally
- Leave blank for videos without transcription
- Identify and mark intro and outro in chapters section

For each short video (1-20):
Title for video[number]:
Description for video[number]:
Tags for video[number] (a list separated by commas):

if the transciption of the trailer is not avalable, write the title, description and tags for the trailer video based on the full transcription.
this is only applicable for the trailer video, not for the short videos.

"""

def transcribe_audio_file(client, file_path):
    """Transcribe a single audio file using Groq API"""
    try:
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(file_path.name, file.read()),
                model="whisper-large-v3",
                response_format="text"
            )
        return transcription
    except Exception as e:
        return f"Error transcribing {file_path.name}: {str(e)}"

def process_audio_files(folder_path):
    """Process all MP3 files in the given folder"""
    transcriptions = {}
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        folder = Path(folder_path)
        
        # Check if folder exists
        if not folder.exists():
            st.error(f"Folder {folder_path} does not exist")
            return transcriptions
        
        # Process files from 1.mp3 to 20.mp3
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        files_found = 0
        for i in range(1, 21):
            file_name = f"{i}.mp3"
            file_path = folder / file_name
            
            if file_path.exists():
                files_found += 1
        
        if files_found == 0:
            st.warning("No MP3 files found in the specified folder")
            return transcriptions
        
        processed = 0
        for i in range(1, 21):
            file_name = f"{i}.mp3"
            file_path = folder / file_name
            
            if file_path.exists():
                status_text.text(f"Transcribing {file_name}...")
                transcription = transcribe_audio_file(client, file_path)
                transcriptions[i] = transcription
                processed += 1
                progress_bar.progress(processed / files_found)
            else:
                # Skip missing files without error
                continue
        
        progress_bar.empty()
        status_text.empty()
                
    except Exception as e:
        st.error(f"Error processing audio files: {str(e)}")
    
    return transcriptions

def format_output(podcast_name, guest_name, episode_number, 
                 instruction_prompt, full_transcription, transcriptions, additional_details):
    """Format the output according to specifications"""
    
    output = []
    
    # Header section
    output.append(f"Podcast: {podcast_name}")
    output.append(f"Guest: {guest_name}")
    output.append(f"Episode: {episode_number}")
    output.append("")
    output.append("=" * 80)
    output.append("")
    
    # Instruction prompt
    output.append("INSTRUCTION PROMPT:")
    output.append("-" * 40)
    output.append(instruction_prompt)
    output.append("")
    output.append("=" * 80)
    output.append("")
    
    # Full transcription
    output.append("FULL TRANSCRIPTION:")
    output.append("-" * 40)
    output.append(full_transcription)
    output.append("")
    output.append("=" * 80)
    output.append("")
    
    # Short video transcriptions
    output.append("SHORT VIDEO TRANSCRIPTIONS:")
    output.append("-" * 40)
    output.append("")
    
    for i in range(1, 21):
        if i in transcriptions and transcriptions[i]:
            output.append(f"Short Video {i}:")
            output.append(transcriptions[i])
            output.append("")
    
    # Additional details
    if additional_details:
        output.append("=" * 80)
        output.append("")
        output.append("ADDITIONAL DETAILS:")
        output.append("-" * 40)
        output.append(additional_details)
    
    return "\n".join(output)

def save_to_file(content, file_path):
    """Save content to a text file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return False

# Main UI
st.title("🎙️ Podcast Transcription & SEO Generator")
st.markdown("---")

# Create two columns for input fields
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 Podcast Information")
    
    # Podcast dropdown
    selected_podcast = st.selectbox(
        "Select Podcast",
        options=list(PODCAST_DATA.keys()),
        help="Choose from the available podcasts"
    )
    
    # Guest name
    guest_name = st.text_input(
        "Guest Name",
        placeholder="Enter the guest's name",
        help="Name of the guest featured in this episode"
    )
    
    # Episode number
    episode_number = st.text_input(
        "Episode Number",
        placeholder="e.g., 001, 42, 156",
        help="Episode number for this podcast"
    )

with col2:
    st.subheader("📁 File Settings")
    
    # File location
    file_location = st.text_input(
        "Audio Files Location",
        placeholder="C:/path/to/files or J:/main/work/0098/videos",
        help="Full path to folder with MP3 files. Windows example: J:\\main\\work\\0098\\videos"
    )
    
    # Show API key status
    st.success("✅ API Key loaded from .env file")

# Full width sections
st.markdown("---")
st.subheader("📝 Content Configuration")

# Instruction prompt
instruction_prompt = st.text_area(
    "Instruction Prompt",
    value=DEFAULT_INSTRUCTION_PROMPT,
    height=250,
    help="Detailed instructions for content generation"
)

# Full transcription
full_transcription = st.text_area(
    "Full Transcription",
    placeholder="Paste the full podcast transcription here...",
    height=200,
    help="Complete transcription of the full podcast episode"
)

# Additional details
additional_details = st.text_area(
    "Additional Details (Optional)",
    placeholder="Any additional information or notes...",
    height=100,
    help="Optional additional details to include in the output"
)

st.markdown("---")

# Single action button
if st.button("🚀 Process & Generate Output", type="primary", use_container_width=True):
    # Validate inputs
    if not selected_podcast:
        st.error("Please select a podcast")
    elif not guest_name:
        st.error("Please enter the guest name")
    elif not episode_number:
        st.error("Please enter the episode number")
    elif not file_location:
        st.error("Please enter the audio files location")
    elif not instruction_prompt:
        st.error("Please provide instruction prompt")
    elif not full_transcription:
        st.error("Please provide full transcription")
    else:
        with st.spinner("Processing..."):
            # Store file location in session state
            st.session_state.file_location = file_location
            
            # Step 1: Process audio files
            st.info("📊 Step 1/3: Transcribing audio files...")
            transcriptions = process_audio_files(file_location)
            st.session_state.transcriptions = transcriptions
            
            if transcriptions:
                st.success(f"✅ Successfully transcribed {len(transcriptions)} files!")
            else:
                st.warning("⚠️ No audio files were transcribed. Continuing with output generation...")
            
            # Step 2: Generate formatted output
            st.info("📝 Step 2/3: Generating formatted output...")
            formatted_output = format_output(
                PODCAST_DATA[selected_podcast],  # Pass description instead of name
                guest_name,
                episode_number,
                instruction_prompt,
                full_transcription,
                st.session_state.transcriptions,
                additional_details
            )
            st.session_state.formatted_output = formatted_output
            
            # Step 3: Save to the same location as audio files
            st.info("💾 Step 3/3: Saving generated prompt...")
            output_file_path = Path(file_location) / "generated_prompt.txt"
            
            if save_to_file(formatted_output, output_file_path):
                st.success(f"✅ Generated prompt saved to: {output_file_path}")
            else:
                st.error("❌ Failed to save the generated prompt file")
            
            st.success("✅ All steps completed successfully!")

# Display results
if st.session_state.formatted_output:
    st.markdown("---")
    st.subheader("📤 Generated Output")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Preview", "Export Options"])
    
    with tab1:
        # Display in a text area for preview
        st.text_area(
            "Output Preview",
            value=st.session_state.formatted_output,
            height=400,
            disabled=True
        )
    
    with tab2:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Copy section
            st.markdown("**📋 Copy to Clipboard**")
            st.code(st.session_state.formatted_output[:500] + "...", language=None)
            st.info("Click above and use Ctrl+A to select all")
        
        with col2:
            # Save to file
            st.markdown("**💾 Save to Different Location**")
            
            if st.button("Save to Current Directory", use_container_width=True):
                if save_to_file(st.session_state.formatted_output, "generated_prompt.txt"):
                    st.success(f"Saved to generated_prompt.txt")
        
        with col3:
            # Show current save location
            st.markdown("**📁 Auto-saved Location**")
            if st.session_state.file_location:
                saved_path = Path(st.session_state.file_location) / "generated_prompt.txt"
                st.info(f"Already saved to:\n{saved_path}")
            else:
                st.info("Will be saved to audio files location after processing")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Podcast Transcription & SEO Generator v1.0 | 
        Built with Streamlit & Groq API
    </div>
    """,
    unsafe_allow_html=True
)