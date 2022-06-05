# Real_Time_Contro_System_GUI
The GUI tool for CW-CNN based prosthetic hand real-time control system.   
To use it, you must have `SMK 32 channels multi-array electrodes device`.  

How to build environment:
--------------------
1. cd to your project file
2. git clone https://github.com/ZixuanQIN/Real_Time_Contro_System_GUI.git
3. mkdir model (to build a file named "model", it should be in the same path as the "RealTimeControlSystem" folder)
4. cd RealTimeControlSystem
5. pip3 install -r requirements.txt

How to use:
--------------------
1. cd RealTimeControlSystem.
2. python3 RealTimeSystem.py.
3. click "Open Signal Monitor".
4. click "Start SMK Device", and select the port to which the SMK is connected in the terminal or command prompt, and enter. When you can see the EMG signal data stream, go back to the GUI tool and click "Start".
5. The next step please refer to the supplimentary matrial "Movie S1" to check the usage of the GUI tool.
