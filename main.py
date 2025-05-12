import os
import ast
import cloudinary
import cloudinary.uploader
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize cloudinary once
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def generate_and_save_code(prompt, filename):
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Generate the response
    response = client.chat.completions.create(  # FIX 1: Use chat.completions.create not responses.create
        model="gpt-4.1",  # Or "gpt-4.0" depending on your access
        messages=[
            {
                "role": "system",
                "content": ("You are an expert in writing manim code. Only output JSON like "
                            "{'code':'python code here', 'scene_name':'scene name here'} "
                            "without any explanation. If asked anything else, say 'I can't help you with that.'")
            },
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the content
    output_text = response.choices[0].message.content.strip()
    
    # Parse the JSON safely
    try:
        output_dict = ast.literal_eval(output_text)
    except Exception as e:
        st.error(f"Error parsing OpenAI response: {e}")
        return None

    # Save code to file
    try:
        with open(filename, 'w') as f:
            f.write(output_dict['code'])
    except Exception as e:
        st.error(f"Error saving code: {e}")
        return None

    return output_dict

def upload_video(scene_name):
    video_path = f"media/videos/illustration/1080p60/{scene_name}.mp4"
    
    if not os.path.exists(video_path):
        st.error(f"Video file not found: {video_path}")
        return None

    upload_result = cloudinary.uploader.upload(
        video_path,
        resource_type="video",
        folder="generated_videos"
    )
    return upload_result.get('secure_url')

# Streamlit app
st.title("Manim Illustration Generator 🚀")

prompt = st.text_input("Enter your illustration prompt:") + "Show step by step animation of the illustration with text"

if st.button("Generate"):
    if prompt:
        with st.spinner("Generating Manim code..."):
            filename = "illustration.py"
            output_dict = generate_and_save_code(prompt, filename)

            if output_dict:
                scene_name = output_dict['scene_name']

                # Render Manim scene
                with st.spinner("Rendering video..."):
                    exit_code = os.system(f"manim {filename} {scene_name}")
                    if exit_code != 0:
                        st.error("Manim rendering failed.")
                    else:
                        with st.spinner("Uploading video..."):
                            video_url = upload_video(scene_name)
                            if video_url:
                                st.success("Video uploaded successfully!")
                                st.video(video_url)
                                st.write("Video URL:", video_url)

                                # Clean up
                                os.system("rm -rf media")
                            else:
                                st.error("Video upload failed.")
    else:
        st.warning("Please enter a prompt to continue.")
