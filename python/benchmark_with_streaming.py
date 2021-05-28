'''
Introduction

receive video from Demo_Viedo(default)/gstreamer streaming
and process object detection and resend to others
'''
import time
import torch
import torch.nn as nn
import torchvision.models as models
from torch.autograd import Variable
import cv2 as cv
import numpy as np

#get pretrained model
model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
#set device
if torch.cuda.is_available():
    print('Cuda avilable',torch.cuda.get_device_name(0))
    model=model.to('cuda')
else:
    print('cuda is not avilable')
#set inference
model.eval()

def get_bbox(frame,model):
    #preprocess frame
    frame=frame.reshape(1,frame.shape[2],frame.shape[0],frame.shape[1])
    frame=frame/255
    #set device
    if torch.cuda.is_available():
        frame=torch.cuda.FloatTensor(frame)
    else:
        frame=torch.FloatTensor(frame)
    return model(frame)

'''
For receive image, you have to change VideoCapure init
'''
#cap = cv.VideoCapture('udpsrc port=9777 ! application/x-rtp ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! appsink', cv.CAP_GSTREAMER)
cap = cv.VideoCapture('srtsrc uri="srt://192.168.0.14:9777?mode=caller" ! application/x-rtp ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! videoscale ! appsink', cv.CAP_GSTREAMER)
#cap = cv.VideoCapture('https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm')
'''
For sending image, you have to set ip and port number and run receiver.py at target
'''
out = cv.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency ! rtph264pay mtu=1316 ! srtsink uri="srt://:9888?mode=listener"', 0, 30, (224, 224))

if not cap.isOpened():
    print("VideoCapture not opened")
    exit(-1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("empty frame")
        break
    t1 = time.time()
    #process object detection
    predictions = get_bbox(frame,model)
    t2 = time.time()
    print('Inference time: %6.2fms' % ( (t2-t1)*100))
    scores=predictions[0]['scores']
    boxes=predictions[0]['boxes']
    img=frame
    for i in range(len(scores)):
        if scores[i] > 0.5:
            img=cv.rectangle(frame,(int(boxes[i][0]),int(boxes[i][1])),
            (int(boxes[i][2]),int(boxes[i][3])),(0,255,0),3)
        
    cv.imshow("Result", img) #show image with opencv
    out.write(img)
    if cv.waitKey(1) == 27:
        break


cap.release()
cv.destroyWindow("Receiver")
