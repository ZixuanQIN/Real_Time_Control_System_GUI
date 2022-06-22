# Real_Time_Control_System_GUI
The GUI tool for CW-CNN based prosthetic hand real-time control system.   
**Important:**   
Due to the **Confidential Agreement**, the **AT Commands** of SMK multi-array eletrode are secret. We deleted the class named "SerialPort". Please build your own EMG acquisition program based on LSL, and modify the corresponding part in the **SMK_LSL_START() function from module/GUI.py, line218-247**.
If you don't familiar with LSL (lab streaming layer), please refer to this repositories: https://github.com/sccn/labstreaminglayer 

You can also change the CW-CNN model to your proposal method, please remember to modify the input and output size accordingly.  

## About this repository:
-------------------------
This repository is one of the Supplementary Materials of our journal paper "**A CW-CNN Regression Model-based Real-Time System for Virtual Hand Control**", named "**Source Code S1**". You can simply use it for real-time sEMG signal observation; Or you can train a model by yourself, update the model using transfer learning in different days, then load the trained model to this GUI tool, and connect to robot or virtual hand for real-time implementation.  

The paper link:  

**- Required Device:** SMK Multi-Array Electrode Device (32 channels)  If you have your own device, please revise the code accordingly, including the input/output size and data acquisition program.  
**- Optional:** Virtual Hand program or real Prosthetic Hand

## How to build environment:
-------------------------
1. cd to the path of your project folder
2. git clone https://github.com/ZixuanQIN/Real_Time_Control_System_GUI.git
3. mkdir model (to build an empty folder named "model", it should be in the same path as the "RealTimeControlSystem" folder)
4. cd RealTimeControlSystem
5. pip3 install -r requirements.txt

## How to use:
-------------------------
1. cd RealTimeControlSystem.
2. python3 RealTimeSystem.py.
3. click "Open Signal Monitor".
4. click "Start SMK Device", and select the port to which the SMK is connected in the terminal or command prompt, and enter. When you can see the EMG signal data stream, go back to the GUI tool and click "Start". (If you use another device for EMG acquisition, you can change the name of this botton. This part can be revised from module/GUI.py, line218-247)
5. About the next steps, please refer to the supplimentary matrial "Movie S1" to check the usage of the GUI tool.
