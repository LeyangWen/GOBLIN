import os
import cv2
from pytube import YouTube

# Function to download a YouTube video based on the URL
def download_video(url, output_folder, video_name):
    try:
        # Create a YouTube object with the URL
        youtube = YouTube(url)

        # Select the highest resolution available
        video = youtube.streams.get_highest_resolution()

        # Download the video to the output folder
        video_path = video.download(output_path=output_folder, filename=video_name+'.mp4')

        print("Video downloaded successfully!")
        return video_path

    except Exception as e:
        print("Error:", str(e))
        return None


# Function to save every 50th frame of a video as a JPG image
def save_frames(video_path, frames_folder):
    try:
        # Create a directory to store the frames
        if not os.path.exists(frames_folder):
            os.makedirs(frames_folder)

        # Open the video file
        cap = cv2.VideoCapture(video_path)

        frame_count = 0
        frame_number = 0

        # Read and save frames
        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1
            
            # Save every 10th frame
            if frame_count % 10 == 0:
                frame_path = os.path.join(frames_folder, f"frame_{frame_number}.jpg")
                cv2.imwrite(frame_path, frame)
                #print(frame_path)
                frame_number += 1

        cap.release()
        print("Frames saved successfully!")

    except Exception as e:
        print("Error:", str(e))


# Read the URLs from the video list file
with open("E:/Datathon/VideoList.txt", "r") as file:
    video_urls = file.read().splitlines()

processed_videos = set()

# Read the processed video URLs from the file
if os.path.exists("E:/Datathon/ProcessedVideoList.txt"):
    with open("E:/Datathon/ProcessedVideoList.txt", "r") as file:
        processed_videos = set(file.read().splitlines())

# Iterate through each video URL
for url in video_urls:
    # Check if the URL is already processed
    if url in processed_videos:
        print(f"Video '{url}' is already processed. Skipping...")
        continue

    # video name
    video_name = url.split('=')[1]

    # Download the video
    video_path = download_video(url, "E:/Datathon/DownloadedVideos", video_name)

    if video_path:
        # Get the video file name
        video_filename = os.path.basename(video_path)

        # Create a folder with the video's filename
        #frames_folder = os.path.splitext(video_filename)[0]
        frames_folder = url.split('=')[1]
        frames_folder_path = os.path.join("E:/Datathon/Frames", frames_folder)
        os.makedirs(frames_folder_path, exist_ok=True)

        # Save every 50th frame of the video as JPG images
        save_frames(video_path, frames_folder_path)

        # Append the processed video URL to the file
        with open("E:/Datathon/ProcessedVideoList.txt", "a") as file:
            file.write(url + "\n")

        print(f"Video '{url}' processed successfully.")

    print()

'''
# Add the first URL to the processed list if it is not already present
if video_urls and video_urls[0] not in processed_videos:
    with open("ProcessedVideoList.txt", "a") as file:
        file.write(video_urls[0] + "\n")
'''
print("All videos processed!")
