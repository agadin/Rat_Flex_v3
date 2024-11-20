# Current Instructions

1. Turn on raspberry pi
2. hit the folder icon in the top left corner of the screen next to the globe
3. `/home/ratflex` should open
4. On the `Rat_Flex_v3 folder`, right click and select "Open in Terminal"
5. In the terminal, type `source base/bin/activate` and hit enter 
6. type in `python protocol_runner.py` and hit enter
7. Repeat step 4 to open a second terminal
8. In the terminal, type `source base/bin/activate` and hit enter 
9. Type `streamlit run simple_main.py` and hit enter 

# Viewing the data
Inside the Rat_Flex_v3 folder, there is a `.csv` called `data.csv` that conatins all data from the device. NOTE: This file is NOT overwritten so you will have to clear it manually if you want to start fresh. To do this open the file in a text editor and delete all the contents and save it.
