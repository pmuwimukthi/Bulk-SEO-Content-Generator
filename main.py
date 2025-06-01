import os
import streamlit as st
from groq import Groq
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def transcribe_audio(client, file_path, index):
    try:
        with open(file_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(f"{index}.mp3", f),
                model="whisper-large-v3",
                response_format="text",
            )
            return transcription
    except Exception as e:
        st.error(f"Error processing {file_path}: {e}")
        return "[Transcription Error]"

def generate_prompt(inputs):
    prompt = []
    prompt.append(inputs['podcast_details'])
    prompt.append("\n" + inputs['instructions'])
    if inputs['optional_note'].strip():
        prompt.append("\n" + inputs['optional_note'])
    
    prompt.append("\n\nTranscripts:")
    for idx, transcript in enumerate(inputs['transcripts'], start=1):
        prompt.append(f"\nvideo {idx}\ntranscription: {transcript}")
    
    prompt.append("\n\nexpected output:")
    prompt.append("""title for full podcast:
description for full podcast:
tags for full podcast (a list separated by commas):

""")
    for i in range(1, 21):
        prompt.append(f"""title for video{i}:
description for video{i}:
tags for video{i} (a list separated by commas):

""")
    return "\n".join(prompt)

def main():
    st.title("Bulk SEO Content Generator")

    with st.form("input_form"):
        podcast_details = st.text_area("Podcast Details (required):", height=150)
        instructions = st.text_area("General Instructions:", 
                                  value="""Generate SEO-optimized titles, detailed descriptions, and relevant tags. we expect longe and detailed discription for each one of the videos specially the full video. Tags should be comma-separated.
                                  if transcription is not available don't write anything for that video.""",
                                  height=150)
        optional_note = st.text_area("Optional Note:", height=100)
        input_dir = st.text_input("MP3 Files Directory Path:")
        
        submitted = st.form_submit_button("Generate Content")

    if submitted:
        if not input_dir or not os.path.isdir(input_dir):
            st.error("Invalid directory path")
            return

        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Process MP3 files
        transcripts = []
        for i in range(1, 21):
            mp3_path = os.path.join(input_dir, f"{i}.mp3")
            if os.path.exists(mp3_path):
                transcript = transcribe_audio(groq_client, mp3_path, i)
                transcripts.append(transcript)
            else:
                transcripts.append("[No audio file found]")

        # Build prompt
        inputs = {
            'podcast_details': podcast_details,
            'instructions': instructions,
            'optional_note': optional_note,
            'transcripts': transcripts
        }
        full_prompt = generate_prompt(inputs)

        # Generate content with OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1",  # Update to correct model name as needed
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=4000
            )
            generated_text = response.choices[0].message.content
            
            # Save output
            output_path = os.path.join(input_dir, "generated_seo_content.txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(generated_text)
            
            st.success(f"Content generated successfully! Saved to: {output_path}")
            st.subheader("Generated Content:")
            st.text_area("Output", generated_text, height=500)
            
        except Exception as e:
            st.error(f"Error generating content: {e}")

if __name__ == "__main__":
    main()
