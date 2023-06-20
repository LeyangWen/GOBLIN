import os
import glob
import cv2
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
import shutil
import random
import keyboard, threading, time



def add_gaussian_noise(image, mean=0, std_dev=10):
    noise = np.random.normal(mean, std_dev, image.shape).astype(np.uint8)
    noisy_image = cv2.add(image, noise)
    return noisy_image

def add_salt_and_pepper_noise(image, salt_vs_pepper=0.5, amount=0.04):
    h, w = image.shape[:2]
    num_salt = int(h * w * amount * salt_vs_pepper)
    num_pepper = int(h * w * amount * (1.0 - salt_vs_pepper))

    # Generate random coordinates for salt noise
    salt_coords = np.array([np.random.randint(0, i, num_salt) for i in (h, w)])
    image[salt_coords[0], salt_coords[1]] = 255

    # Generate random coordinates for pepper noise
    pepper_coords = np.array([np.random.randint(0, i, num_pepper) for i in (h, w)])
    image[pepper_coords[0], pepper_coords[1]] = 0

    return image


if True:
    
    # Specify the directory path
    video_root = './Frames/'
    label_root = './Labels/'

    # Use glob to retrieve folder names
    #video_folders = glob.glob(label_directory + '*')

    video_folders = [folder for folder in glob.glob(label_root + '*') if os.path.isdir(folder)]

    video_names = []

    # Print the folder names
    for folder in video_folders:
        video_names.append(folder.split('\\')[1])
        print(folder.split('\\')[1])


    for vid_idx in range(len(video_names)):

    
        image_directory = video_root + video_names[vid_idx]
        label_directory = label_root + video_names[vid_idx]

        # Get the list of image file paths in the image directory
        image_files = glob.glob(os.path.join(image_directory, '*.jpg'))

        for image_idx in range(len(image_files)):
 

            image_path = image_files[image_idx]

            image = cv2.imread(image_path)

            image_name = os.path.basename(image_path)

            label_file_path = os.path.join(label_directory, os.path.splitext(image_name)[0] + ".txt")

            # Add Gaussian noise
            noisy_image_gaussian = add_gaussian_noise(image.copy(), mean=0, std_dev=0.5)
            gaussian_label_path = os.path.join(label_directory, 'gaussian_' + os.path.splitext(image_name)[0] + ".txt")
            gaussian_image_path = os.path.join(image_directory, 'gaussian_' + os.path.splitext(image_name)[0] + ".jpg")


            # Add salt and pepper noise
            noisy_image_sp = add_salt_and_pepper_noise(image.copy(), salt_vs_pepper=0.5, amount=0.05)
            sp_label_path = os.path.join(label_directory, 'salt_pepper_' + os.path.splitext(image_name)[0] + ".txt")
            sp_image_path = os.path.join(image_directory, 'salt_pepper_' + os.path.splitext(image_name)[0] + ".jpg")



            shutil.copy2(label_file_path, gaussian_label_path)
            shutil.copy2(label_file_path, sp_label_path)

            print('\nLabels are successfully copied...')
            print("Original Label: %s" % label_file_path)
            print("Gaussian Label: %s" % gaussian_label_path)
            print("Salt&Pepper Label: %s" % sp_label_path)

            cv2.imwrite(gaussian_image_path, noisy_image_gaussian)
            cv2.imwrite(sp_image_path, noisy_image_sp)

            print('\nImages are successfully saved...')
            print("Original Image: %s" % image_path)
            print("Gaussian Image: %s" % gaussian_image_path)
            print("Salt&Pepper Image: %s" % sp_image_path)


            #cv2.imshow('ori', image)
            #cv2.imshow('gauss', noisy_image_gaussian)
            #cv2.imshow('sp', noisy_image_sp)
            #cv2.waitKey(0)









