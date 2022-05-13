### importing required libraries
import gc
from json.encoder import INFINITY
import torch
import cv2
from time import time
import win32api, win32con
import pyautogui
import numpy as np
import keyboard
from pynput.mouse import Button, Controller
import mss
from math import sqrt
import gc
from pathlib import Path

aimbot = True
triggerBot = False

screenShotWidth = 416
screenShotHeight = 416

headshot_mode = True

videoGameWindowTitle = "Halo Infinite"

movement_amp = 1

sct = mss.mss()

### -------------------------------------- function to run detection ---------------------------------------------------------
def detectx (frame, model):
    frame = [frame]
    #print(f"[INFO] Detecting. . . ")
    results = model(frame)
    # results.show()
    # print( results.xyxyn[0])
    # print(results.xyxyn[0][:, -1])
    # print(results.xyxyn[0][:, :-1])

    labels, cordinates = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]

    return labels, cordinates

### ------------------------------------ to plot the BBox and results --------------------------------------------------------
def plot_boxes(results, frame, area, classes):

    """
    --> This function takes results, frame and classes
    --> results: contains labels and coordinates predicted by model on the given frame
    --> classes: contains the strting labels

    """
    labels, cord = results
    n = len(labels)
    x_shape, y_shape = frame.shape[1], frame.shape[0]

    #print(f"[INFO] Total {n} detections. . . ")
    #print(f"[INFO] Looping through all detections. . . ")

    highest_confidence_detection = None
    highest_confidence = 0

    closest_mouse_dist = INFINITY
    
    cWidth = area["width"] / 2
    cHeight = area["height"] / 2

    mouse = Controller()

    ### looping through to find closest target to mouse
    for i in range(n):
        row = cord[i]
        if row[4] >= 0.65: ### threshold value for detection. We are discarding everything below this value
            x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape) ## BBOx coordniates

            ### Check dist to mouse and if closest select this
            centerx = x1 - (0.5*(x1-x2))
            centery = y1 - (0.5*(y1-y2))

            centerx = centerx - cWidth
            centery = centery - cHeight

            current_mouse_pos = mouse.position
            
            dist = sqrt((current_mouse_pos[0]-centerx)**2 + (current_mouse_pos[1]-centery)**2)
            
            if dist < closest_mouse_dist and classes[int(labels[i])] == 'enemy' or dist < closest_mouse_dist and classes[int(labels[i])] == 0:
                highest_confidence_detection = row
                closest_mouse_dist = dist

            ### Check confidence and select if highest confidence
            #if row[4] > highest_confidence and classes[int(labels[i])] == 'enemy' or row[4] > highest_confidence and classes[int(labels[i])] == 'person':
                #highest_confidence_detection = row
                #highest_confidence = highest_confidence_detection[4]

            # Draw bbox for this detection    
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) ## BBox        

    if highest_confidence_detection is not None:
        x1, y1, x2, y2 = int(highest_confidence_detection[0]*x_shape), int(highest_confidence_detection[1]*y_shape), int(highest_confidence_detection[2]*x_shape), int(highest_confidence_detection[3]*y_shape) ## BBOx coordniates

        box_height = y1 - y2

        if headshot_mode == True:
            headshot_offset = box_height * 0.35
        else:
            headshot_offset = box_height * 0.2    
                
        centerx = x1 - (0.5*(x1-x2))
        centery = y1 - (0.5*(y1-y2))

        centerx = centerx - cWidth
        centery = (centery + headshot_offset) - cHeight

        posx = pyautogui.position().x # Not working
        posy = pyautogui.position().y # Not working

        if aimbot == True:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(centerx * movement_amp), int(centery * movement_amp), 0, 0)

        if x1 <= posx and posx <= x2 and y1 <= posy and posy <= y2 and triggerBot == True:
            # Point is in bounding box
            mouse.click(Button.left, 1)

    #print(f"[INFO] Finished extraction, returning frame!")
    return frame

### ---------------------------------------------- Main function -----------------------------------------------------

def main(vid_out = None, run_loop=False):

    print(f"[INFO] Loading model... ")
    ## loading the custom trained model
    model = torch.hub.load('yolov5', 'custom', source ='local', path='last.pt', force_reload=True) # The repo is stored locally

    classes = model.names ### class names in string format

    if run_loop==True:

        # Selecting the correct game window
        try:
            videoGameWindows = pyautogui.getWindowsWithTitle(videoGameWindowTitle)
            videoGameWindow = videoGameWindows[0]
        except:
            print("The game window you are trying to select doesn't exist.")
            print("Check variable videoGameWindowTitle (typically on line 19")
            exit()

        # Select that Window
        videoGameWindow.activate()

        sctArea = {"mon": 1, "top": videoGameWindow.top + (videoGameWindow.height - screenShotHeight) // 2,
                         "left": ((videoGameWindow.left + videoGameWindow.right) // 2) - (screenShotWidth // 2),
                         "width": screenShotWidth,
                         "height": screenShotHeight}

        if vid_out: ### creating the video writer if video output path is given
            # by default VideoCapture returns float instead of int
            width = int(screenShotWidth)
            height = int(screenShotHeight)
            fps = int(20)
            codec = cv2.VideoWriter_fourcc(*'mp4v') ##(*'XVID')
            out = cv2.VideoWriter(vid_out, codec, fps, (width, height))

        frame_no = 1

        #cv2.namedWindow("vid", cv2.WINDOW_NORMAL)

        count = 0
        sTime = time()
        
        while True:
            img = sct.grab(sctArea)

            img = np.array(img)

            frame = img

            #print(f"[INFO] Working with frame {frame_no} ")

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            results = detectx(frame, model = model)          
            frame = plot_boxes(results, frame, sctArea, classes = classes)
                
            #cv2.imshow("vid", frame)

            if vid_out:
                #print(f"[INFO] Saving output video. . . ")
                out.write(frame)

            if cv2.waitKey(1) and 0xFF == 27:
                break

            if keyboard.is_pressed('esc'):
                print(f"[INFO] Exiting. . . ")               
                if vid_out:
                    out.release()
                break

            frame_no += 1

            # Forced garbage cleanup every second
            count += 1
            if (time() - sTime) > 1:
                print("CPS: {}".format(count))
                count = 0
                sTime = time()

                gc.collect(generation=0)

        print(f"[INFO] Cleaning up. . . ")
        
        ## closing all windows
        exit()  



### -------------------  calling the main function-------------------------------

#main(run_loop=True, vid_out="ai_sight.mp4")
main(run_loop=True)
            

