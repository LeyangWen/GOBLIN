import os
import glob
import cv2
import numpy as np
import tkinter as tk
from PIL import ImageTk, Image
import shutil
import random
import keyboard, threading, time

from decimal import Decimal, getcontext


# set the desired precision
getcontext().prec = 28


win_or_mac = ''
while win_or_mac != 'w' and win_or_mac != 'm':
    print('\n\nIs your OS Window (w) or Mac (m)?')
    win_or_mac = input()


# Global variables for tracking mouse events and bounding box
drawing = False
start_x, start_y = -1, -1
bounding_boxes = []
rectangles = []

boxes_to_remove = []

edit_mode = ''    # remove box / add box / delete image

CLASSES = ['Cranes', 'Excavators', 'Bulldozers', 'Scrapers', 'Trucks', 'Construction Workers']

class_counts = np.zeros(len(CLASSES))

curr_label = 0

done = 0

image_already_checked = 0

def init():
    global image, ori_image, start_x, start_y,end_x,end_y, rectangles, refPt, edit_mode
    global scaling_factor, boxes_to_remove, bounding_boxes, class_counts, curr_label

    drawing = False
    start_x, start_y,end_x,end_y = -1, -1, -1, -1
    bounding_boxes = []
    rectangles = []

    boxes_to_remove = []

    edit_mode = ''

    refPt = []

    class_counts = np.zeros(len(CLASSES))
    curr_label = 0


# Create a function to load and display the image
def load_image(image_path):
    # Load the image using OpenCV
    global image, ori_image, start_x, start_y,end_x,end_y, rectangles, refPt, edit_mode, label_file_path, curr_image_path
    global scaling_factor, boxes_to_remove, bounding_boxes, class_counts, curr_label, curr_image_idx, label_file_path, original_height, original_width
    global image_already_checked, curr_image_in_dest, curr_label_in_dest

    init()
    image = cv2.imread(image_path)

    curr_image_path = image_path

    # Get the original image dimensions
    original_height, original_width = image.shape[:2]

    window_height, window_width = 900, 900

    # Calculate the scaling factor based on height or width
    scaling_factor = min(Decimal(window_width) / Decimal(original_width), Decimal(window_height) / Decimal(original_height))
    #print(scaling_factor)

    # Resize the image while preserving the aspect ratio
    resized_height = int(Decimal(original_height) * Decimal(scaling_factor))
    resized_width = int(Decimal(original_width) * Decimal(scaling_factor))
    image = cv2.resize(image, (resized_width, resized_height))

    ori_image = image.copy()

    # Check if the image is listed in the checkedImages.txt file
    
    image_name = os.path.basename(image_path)
    
    '''
    if is_image_listed(image_name):
        print("Image is already listed in checkedImages.txt:", image_name)
        curr_image_idx += 1
        return
    else:
        print("Current Image: ", image_name)
    '''

    # Check if there is a corresponding label file
    label_file_path = os.path.join(label_directory, os.path.splitext(image_name)[0] + ".txt")
    if os.path.isfile(label_file_path):
        # Read label file and draw bounding boxes
        with open(label_file_path, 'r') as label_file:
            for line in label_file:
                if line.strip() == '':
                    break
                class_id, center_x, center_y, width, height = map(Decimal, line.split())

                class_id = int(class_id)
                
                if center_x <= 1 and center_y <=1 and width <=1 and height <=1: # YOLO Format
                    image_already_checked = 1
                    # convert YOLO format into typical bounding box format
                    x = ((Decimal(center_x) - Decimal(width)/Decimal(2)) * Decimal(original_width))
                    y = ((Decimal(center_y) - Decimal(height)/Decimal(2)) * Decimal(original_height))
                    w = (Decimal(width) * Decimal(original_width))
                    h = (Decimal(height) * Decimal(original_height))
                else:   #Patrick's format
                        
                    if int(class_id) == 5: # truck
                        class_id = CLASSES.index('Trucks')
                    elif int(class_id) == 4: # worker
                        class_id = CLASSES.index('Construction Workers')
                    elif int(class_id) == 1: # excavator
                        class_id = CLASSES.index('Excavators')
                    elif int(class_id) == -1: # assume scraper
                        class_id = CLASSES.index('Scrapers')
                    elif int(class_id) == 0:   # cranes 
                        class_id = CLASSES.index('Cranes')
                    elif int(class_id) == 2:    # Bulldozers
                        class_id = CLASSES.index('Bulldozers')
                    elif int(class_id) == 3:    # trucks
                        class_id = CLASSES.index('Trucks')


                    image_already_checked = 0
                    x = Decimal(center_x) - Decimal(width)/Decimal(2)
                    y = Decimal(center_y) - Decimal(height)/Decimal(2)
                    w = Decimal(width)
                    h = Decimal(height)

                # Scale the bounding box coordinates to the resized image
                x = (Decimal(x) * Decimal(scaling_factor))
                y = (Decimal(y) * Decimal(scaling_factor))
                w = (Decimal(w) * Decimal(scaling_factor))
                h = (Decimal(h) * Decimal(scaling_factor))

                if int(class_id) == curr_label:
                    draw_bounding_box(image, x, y, w, h)
                bounding_boxes.append((int(class_id), x,y,w,h))

                class_counts[int(class_id)] += 1

    # Create a window and set the mouse callback
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", mouse_event)

    show_edit_image()
    show_class_image()
    show_vid_img_info()

    # Display the image using OpenCV
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    #curr_image_idx += 1
    return


# Create a function to check if the image is listed in checkedImages.txt
def is_image_listed(image_name):
    with open(checked_images_file, 'r') as checked_images:
        for line in checked_images:
            if line.strip() == image_name:
                return True
    return False


def getCheckpoint():
    global video_names, curr_video_idx, curr_image_idx
    vid_idx, img_idx = 0, 0
    vid_name = ''

    if os.path.isfile(check_point_idx):
        with open(check_point_idx, 'r') as checked_images:
            for line_i, line in enumerate(checked_images):
                if line_i == 0:
                    vid_idx = int(video_names.index(line.strip()))
                    vid_name = line.strip()

                else:
                    if line.strip().split(' ')[0] == vid_name:
                        img_idx = int(line.strip().split(' ')[1])
                        return vid_idx, img_idx
    else:
        curr_video_idx = 0
        curr_image_idx = 0
        #saveCheckpoint()

    return vid_idx, img_idx

def saveCheckpoint():
    global curr_video_idx, curr_image_idx, video_names   

    prevLines = []
    overwritten = 0
    newLine = video_names[curr_video_idx] + ' ' + str(curr_image_idx) + '\n'
    if os.path.isfile(check_point_idx):
        with open(check_point_idx, 'r') as checked_images:
            for line_i, line in enumerate(checked_images):
                if line_i == 0:
                    prevLines.append(video_names[curr_video_idx]+'\n')

                else:
                    if line.strip().split(' ')[0] == video_names[curr_video_idx]:
                        prevLines.append(newLine)
                        overwritten = 1
                    else:
                        prevLines.append(line.strip() + '\n')

    if overwritten == 0:
        prevLines.append(newLine.strip())

    
    with open(check_point_idx, 'w') as checked_images:

        checked_images.writelines(prevLines)

    return 0

def mouse_event(event, x, y, flags, param):
    global refPt, image, start_x, start_y, end_x, end_y
    global edit_mode, boxes_to_remove, curr_label

    

    if event == cv2.EVENT_LBUTTONDOWN:
        if edit_mode == 'Add Box':
            drawing = True
            refPt = [(x, y)]
            start_x, start_y = x, y
        
        elif edit_mode == 'Remove Box':

            for i, rect in enumerate(bounding_boxes):   # bounding_boxes: id, x, y, w, h

                if int(rect[0]) != curr_label:
                    continue

                if rect[1] <= x <= rect[1] + rect[3] and rect[2] <= y <= rect[2] + rect[4]:
                    # Change the color of the clicked rectangle to green

                    if i in boxes_to_remove:    # remove from stack
                        boxes_to_remove.pop(i)
                        draw_bounding_box(image, rect[1], rect[2], rect[3], rect[4])

                    else:    
                        stack_removing_box(image, rect[1], rect[2], rect[3], rect[4])
                        boxes_to_remove.append(i)
                        #print(boxes_to_remove)

                    cv2.imshow("Image", image)
                    #print(bounding_boxes)

                    
    elif event == cv2.EVENT_LBUTTONUP:
        if edit_mode == 'Add Box':
            drawing = False
            refPt.append((x, y))
            end_x, end_y = x,y
            #cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 1)
            #cv2.imshow("Image", image)       
            w = abs(end_x - start_x)
            h = abs(end_y - start_y)
            bounding_boxes.append((curr_label, start_x, start_y, w, h))

            draw_all_boxes(bounding_boxes)


    elif event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
        if edit_mode == 'Add Box':
            clone = image.copy()
            cv2.rectangle(clone, refPt[0], (x, y), (0, 255, 0), 1)
            cv2.imshow("Image", clone)

# Create a function to handle mouse events
def edit_mouse_event(event, x, y, flags, param):
    global rectangles, curr_image_idx, curr_video_idx, image_files, done, video_names
    global edit_image, text_remove, text_add, remove_x, text_y, add_x, text_color, text_font, text_scale, text_thickness, column_width, img_remove, delete_x
    global edit_mode, bounding_boxes, boxes_to_remove, curr_label, label_file_path, curr_image_path, image_directory, image_directory_dest, label_directory_dest, curr_image_in_dest, curr_label_in_dest
    global key_board_run, keyboard_threading, key_x, key_y, key_pressed

    if event == cv2.EVENT_LBUTTONDOWN:

        for i, rect in enumerate(rectangles):
            if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]:
                # Change the color of the clicked rectangle to green
                print("Triggered: " + str(rect[4]))


                if edit_mode == "Remove Box" and rect[4] == "Remove Box":
                    temp = bounding_boxes.copy()
                    bounding_boxes = []
                    for item_i, item in enumerate(temp):
                        if item_i not in boxes_to_remove:
                            bounding_boxes.append(item)

                    boxes_to_remove = []

                    draw_all_boxes(bounding_boxes)
 

                elif edit_mode == "Remove All" and rect[4] == "Remove All":

                    temp = bounding_boxes.copy()
                    bounding_boxes = []
                    
                    for item in temp:
                        if int(item[0]) != int(curr_label):
                            bounding_boxes.append(item)

                    boxes_to_remove = []
                    draw_all_boxes(bounding_boxes)    


                elif edit_mode == 'Delete Image' and rect[4] == 'Delete Image':

                    curr_image_idx += 5

                    try:
                        os.remove(label_file_path)
                        print(f'LABEL File {label_file_path} has been successfully removed.')
                    except OSError as e:
                        print(f"An error occurred while removing file '{label_file_path}': {e}")

                    try:
                        os.remove(curr_image_path)
                        print(f'IMAGE File {curr_image_path} has been successfully removed.')
                    except OSError as e:
                        print(f"An error occurred while removing file '{curr_image_path}': {e}")

                    try:
                        os.remove(curr_image_in_dest)
                        print(f'IMAGE File {curr_image_in_dest} has been successfully removed.')
                    except OSError as e:
                        print(f"An error occurred while removing file '{curr_image_in_dest}': {e}")

                    try:
                        os.remove(curr_label_in_dest)
                        print(f'IMAGE File {curr_label_in_dest} has been successfully removed.')
                    except OSError as e:
                        print(f"An error occurred while removing file '{curr_label_in_dest}': {e}")


                    image_files = glob.glob(os.path.join(image_directory, '*.jpg'))
                    cv2.destroyAllWindows()


                edit_mode = rect[4]
                show_edit_image()

                print(edit_mode)

                if edit_mode == 'Prev Image':
                    
                    curr_image_idx -= 6

                    curr_image_idx = max(0, curr_image_idx)

                    save_boundingbox_to_yolo_format(bounding_boxes)

                    load_image(image_files[curr_image_idx])

                elif edit_mode == 'Next Image':
                    
                    curr_image_idx += 6

                    curr_image_idx = min(curr_image_idx, len(image_files))
                    
                    save_boundingbox_to_yolo_format(bounding_boxes)
             
                    load_image(image_files[curr_image_idx])

                
                elif edit_mode == 'Next Video':
                    
                    curr_video_idx += 1
                    curr_image_idx = 0

                    if curr_video_idx == len(video_names):
                        curr_video_idx -= 1
                        save_boundingbox_to_yolo_format(bounding_boxes)
                        cv2.destroyAllWindows()
                    else:
                        save_boundingbox_to_yolo_format(bounding_boxes)
                        init_dir()
                        load_image(image_files[curr_image_idx])

                elif edit_mode == 'Prev Video':
                    
                    curr_video_idx -= 1
                    curr_image_idx = 0

                    if curr_video_idx < 0:
                        curr_video_idx = 0
                        save_boundingbox_to_yolo_format(bounding_boxes)

                        cv2.destroyAllWindows()
                    else:
                        save_boundingbox_to_yolo_format(bounding_boxes)

                        init_dir()
                        load_image(image_files[curr_image_idx])

                elif edit_mode == 'Exit':
                    save_boundingbox_to_yolo_format(bounding_boxes)

                    done = 1
                    cv2.destroyAllWindows()
                    




def show_vid_img_info():
    global rectangles, edit_mode, curr_image_idx, curr_video_idx, image_files, video_names
    global image_already_checked, curr_image_in_dest, curr_label_in_dest, image_directory_dest, label_directory_dest

    
    image_width, image_height = 200, 200
    column_width, column_height = 200, 200

    info_image = 255*np.ones((image_height, image_width, 3), np.uint8)

    if image_already_checked == 1:
        info_image[:,:,0] = 0
        info_image[:,:,2] = 0

    text1 = video_names[curr_video_idx]
    if win_or_mac == 'w':
        text2 = image_files[curr_image_idx].strip().split('/')[-1].split('\\')[1]
    else:
        text2 = image_files[curr_image_idx].strip().split('/')[-1]
    text3 = '('+str(curr_image_idx+1) + ' / ' + str(len(image_files)) + ')'

    curr_image_in_dest = image_directory_dest + '/' + text2.split('.')[0] + '.jpg'
    curr_label_in_dest = label_directory_dest + '/' + text2.split('.')[0] + '.txt'

    for i in range(1):
        # Calculate the coordinates for each column
        x1 = i * column_width
        x2 = (i + 1) * column_width
        label_size, _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = int((x1 + x2 - label_size[0]) / 2)
        label_y = int((column_height + label_size[1]) / 2)
        cv2.putText(info_image, text1, (label_x, label_y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        label_size, _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = int((x1 + x2 - label_size[0]) / 2)
        label_y = int((column_height + label_size[1]) / 2)
        cv2.putText(info_image, text2, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        label_size, _ = cv2.getTextSize(text3, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = int((x1 + x2 - label_size[0]) / 2)
        label_y = int((column_height + label_size[1]) / 2)
        cv2.putText(info_image, text3, (label_x, label_y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Display the image and set the mouse callback
    cv2.imshow("Info", info_image)


def show_edit_image():
    # Create a blank image of size 200x100
    global rectangles, edit_mode, curr_image_idx, curr_video_idx
    global edit_image, text_remove, text_add, remove_x, text_y, add_x, text_color, text_font, text_scale, text_thickness, column_width, img_remove, delete_x, curr_label, label_rectangles
    
    # Define the column labels
    column_labels = ['Remove Box', 'Remove All', 'Add Box', 'Delete Image', 'Prev Image', 'Next Image', 'Prev Video', 'Next Video', 'Exit']

    num_columns = len(column_labels)

    # Define the image size and column size
    image_width, image_height = 200*num_columns, 100
    column_width, column_height = 200, 100
    

    # Create an empty image
    edit_image = np.zeros((image_height, image_width, 3), np.uint8)

    
    rectangles = []
    label_rectangles = []

    # Draw the columns and text labels
    for i in range(num_columns):
        # Calculate the coordinates for each column
        x1 = i * column_width
        x2 = (i + 1) * column_width

        # Draw the column rectangle with black color
        if edit_mode == column_labels[i]:
            cv2.rectangle(edit_image, (x1, 0), (x2, column_height), (0, 255, 0), -1)
        else:
            cv2.rectangle(edit_image, (x1, 0), (x2, column_height), (0, 0, 0), -1)

        rectangles.append((x1,0,column_width,column_height, column_labels[i]))

        # Draw the text label in white color
        label = column_labels[i]
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_x = int((x1 + x2 - label_size[0]) / 2)
        label_y = int((column_height + label_size[1]) / 2)
        cv2.putText(edit_image, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        label_rectangles.append((label_x, label_y))

    # Display the image and set the mouse callback
    cv2.imshow("Edit", edit_image)
    cv2.setMouseCallback("Edit", edit_mouse_event)

    
def show_class_image():
    global class_image, row_height, row_width, row_index, curr_label, class_rectangle, label_x, label_y, label_size, class_counts
    global video_names, curr_video_idx, curr_image_idx, image_files

    # Define the image size and row size
    image_width, image_height = 350, 600
    row_width, row_height = 350, 100
    num_rows = len(CLASSES)

    # Create an empty image
    class_image = np.zeros((image_height, image_width, 3), np.uint8)

    # Define the row labels
    row_labels = CLASSES

    
    class_rectangle = []

    # Draw the rows and text labels
    for i in range(num_rows):
        # Calculate the coordinates for each row
        y1 = i * row_height
        y2 = (i + 1) * row_height

        # Draw the row rectangle with black color
        if curr_label == i:
            cv2.rectangle(class_image, (0, y1), (row_width, y2), (0, 255, 0), -1)
        else:
            cv2.rectangle(class_image, (0, y1), (row_width, y2), (0, 0, 0), -1)


        if True:
            class_rectangle.append((0,y1,row_width,row_height,CLASSES[i]))
            # Draw the text label in white color
            label = row_labels[i] + ' (' + str(int(class_counts[i])) + ')'
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_x = int((row_width - label_size[0]) / 2)
            label_y = int((y1 + y2 + label_size[1]) / 2)
            cv2.putText(class_image, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Display the image and set the mouse callback
    cv2.imshow("Classes", class_image)
    cv2.setMouseCallback("Classes", class_mouse_event)

def class_mouse_event(event, x, y, flags, param):
    global class_image, row_height, row_width, row_index, curr_label, class_rectangle, label_x, label_y, label_size

    if event == cv2.EVENT_LBUTTONDOWN:


        for i, rect in enumerate(class_rectangle):
            if rect[0] <= x <= rect[0] + rect[2] and rect[1] <= y <= rect[1] + rect[3]:
                # Change the color of the clicked rectangle to green
                
                curr_label = i
                print(CLASSES[curr_label])

            
        show_class_image()
        draw_all_boxes(bounding_boxes)

        #cv2.imshow("Classes", class_image)

# convert the bounding_box into YOLO format
# save the bounding_box and image in checked folder as well
def save_boundingbox_to_yolo_format(bounding_boxes):
    global label_file_path, image, original_width, original_height, scaling_factor, curr_image_path
    global curr_video_idx, curr_image_idx, video_names, image_directory_dest, label_directory_dest

    saveCheckpoint()
    
    yolo_boxes = []

    for bounding_box in bounding_boxes:
        cid, x, y, w, h = bounding_box

        x = Decimal(x) / Decimal(scaling_factor)
        y = Decimal(y) / Decimal(scaling_factor)
        w = Decimal(w) / Decimal(scaling_factor)
        h = Decimal(h) / Decimal(scaling_factor)

        center_x = (Decimal(x) + Decimal(w)/2) / Decimal(original_width)
        center_y = (Decimal(y) + Decimal(h)/2) / Decimal(original_height)
        normalized_width = Decimal(w) / Decimal(original_width)
        normalized_height = Decimal(h) / Decimal(original_height)
        yolo_boxes.append((int(cid), center_x, center_y, normalized_width, normalized_height))
        #print([int(cid), center_x, center_y, normalized_width, normalized_height])

    with open(label_file_path, 'w') as curr_label_file:
        for info in yolo_boxes:
            #print(info)
            aLine = ' '.join(map(str,info))
            curr_label_file.write(aLine+'\n')


    checked_image = os.path.join(image_directory_dest, os.path.basename(curr_image_path))
    checked_label = os.path.join(label_directory_dest, os.path.basename(label_file_path))

    shutil.copy2(curr_image_path, checked_image)
    shutil.copy2(label_file_path, checked_label)

    print("Files are successfully saved in the checked folder.")


# Create a function to draw a bounding box on the image
def draw_bounding_box(image, x, y, w, h):
    cv2.rectangle(image, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), 2)

def stack_removing_box(image, x, y, w, h):

    cv2.rectangle(image, (int(x), int(y)), (int(x+w), int(y+h)), (0, 0, 255), 2)

def draw_all_boxes(bounding_boxes):
    global image, ori_image, curr_label, class_counts

    class_counts = np.zeros(len(CLASSES))

    image = ori_image.copy()
    for item in bounding_boxes:
        if item[0] == curr_label:
            draw_bounding_box(image, item[1],item[2],item[3],item[4])


        class_counts[int(item[0])] += 1

    cv2.imshow('Image', image)

    show_edit_image()
    show_class_image()

def init_dir():
    global video_names, curr_video_idx, curr_image_idx, image_directory, label_directory, image_directory_dest, label_directory_dest
    global image_files

    #curr_video_idx, curr_image_idx = getCheckpoint()

    image_directory = './Frames/' + video_names[curr_video_idx]
    label_directory = './Labels/' + video_names[curr_video_idx]

    while not os.path.exists(image_directory):
        curr_video_idx += 1

        image_directory = './Frames/' + video_names[curr_video_idx]
        label_directory = './Labels/' + video_names[curr_video_idx]


    image_directory_dest = './Checked Frames/' + video_names[curr_video_idx]
    label_directory_dest = './Checked Labels/' + video_names[curr_video_idx] 

    if not os.path.exists(image_directory_dest):
        os.makedirs(image_directory_dest)
        print('Directory Created: ' + image_directory_dest)
    if not os.path.exists(label_directory_dest):
        os.makedirs(label_directory_dest)
        print('Directory Created: ' + label_directory_dest)

    # Get the list of image file paths in the image directory
    image_files = glob.glob(os.path.join(image_directory, '*.jpg'))

    #curr_video_idx, curr_image_idx = getCheckpoint()

    #print([curr_video_idx, curr_image_idx])

    return 0

key_board_run = 1
prev_key = ''
# Flag to track the last key press time
last_press_time = 0

# Delay threshold in seconds
delay_threshold = 1.0

def detect_key_press():
    global key_board_run, label_rectangles, last_press_time
    global key_x, key_y, key_event, key_pressed


    while key_board_run == 1:
        
        key_event = keyboard.read_event()

        if key_event.event_type=='down':
            current_time = time.time()

            if current_time - last_press_time >= delay_threshold:

                last_press_time = current_time
                if key_event.name == 'backspace':
                    key_x = label_rectangles[1][0]
                    key_y = label_rectangles[1][1]

                elif key_event.name == 'delete':
                    key_x = label_rectangles[3][0]
                    key_y = label_rectangles[3][1]

                elif key_event.name == 'left':
                    key_x = label_rectangles[4][0]
                    key_y = label_rectangles[4][1]
                elif key_event.name == 'right':
                    key_x = label_rectangles[5][0]
                    key_y = label_rectangles[5][1]
                elif key_event.name == 'up':
                    key_x = label_rectangles[6][0]
                    key_y = label_rectangles[6][1]
                elif key_event.name == 'down':
                    key_x = label_rectangles[7][0]
                    key_y = label_rectangles[7][1]
                elif key_event.name == 'esc':
                    key_x = label_rectangles[8][0]
                    key_y = label_rectangles[8][1]



# Specify the directory path
video_directory = './Frames/'
label_directory = './Labels/'

# Use glob to retrieve folder names
video_folders = glob.glob(label_directory + '*')

video_names = []

# Print the folder names
for folder in video_folders:
    if win_or_mac == 'w':
        video_names.append(folder.split('\\')[1])
        print(folder.split('\\')[1])
    else:
        video_names.append(folder.split('/')[-1])
        print(folder.split('/')[-1])

if not os.path.exists('./Checked Frames'):
    os.makedirs('./Checked Frames')
    print('Directory created: ./Checked Frames')

if not os.path.exists('./Checked Labels'):
    os.makedirs('./Checked Labels')
    print('Directory created: ./Checked Labels')

check_point_idx = './checkpoint.txt'

curr_video_idx, curr_image_idx = getCheckpoint()
#print([video_names[curr_video_idx], curr_image_idx])
'''
image_directory = './Frames/' + video_names[curr_video_idx]
label_directory = './Labels/' + video_names[curr_video_idx]


image_directory_dest = './Checked Frames/' + video_names[curr_video_idx]
label_directory_dest = './Checked Labels/' + video_names[curr_video_idx] 

if not os.path.exists(image_directory_dest):
    os.makedirs(image_directory_dest)
    print('Directory Created: ' + image_directory_dest)
if not os.path.exists(label_directory_dest):
    os.makedirs(label_directory_dest)
    print('Directory Created: ' + label_directory_dest)

# Get the list of image file paths in the image directory
image_files = glob.glob(os.path.join(image_directory, '*.jpg'))
'''
init_dir()

while curr_video_idx < len(video_names) and done==0:
    while curr_image_idx < len(image_files) and done==0:
        load_image(image_files[curr_image_idx])
               

saveCheckpoint()

