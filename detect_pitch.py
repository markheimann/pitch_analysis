import sys
import easygui as g
from aubio import source, pitch
import calculate_tuning
import matplotlib
matplotlib.use('TkAgg') #have to do this in order to use easygui as well
import matplotlib.pyplot as plt
import numpy as np
import math, os
import record_audio

#default settings
AUDIO_DIRECTORY = "audio" #name of directory where all audio files are stored
DIRECTORY = "default"
num_files = len(os.listdir(DIRECTORY)) - 1 #don't count the one where we record deviations
filename = DIRECTORY + "/file" + str(num_files) + ".wav" #store attempts as file1.wav, file2.wav, etc.
ATTEMPT_FILE_NAME = "attempt_info.txt"
loss_file_path = ATTEMPT_FILE_NAME

if len(sys.argv) < 2:
    try:
        #See if user wants to create a new project or add an attempt to an existing project
        var = g.ynbox("Do you want to create a new project?")
        if var: #yes--create new project
            #Create a box for user to add a project title
            DIRECTORY = g.enterbox(msg='Enter a project title', title=' ', default='', strip=True)
            #Create directory with the same name as the user's project title
            DIR_PATH = AUDIO_DIRECTORY + "/" + DIRECTORY
            os.mkdir(DIR_PATH)
            #Create a file to write the tunings and losses on each attempt
            print DIR_PATH, os.listdir(DIR_PATH)
            print len(os.listdir(DIR_PATH)) - 1
        else: #no--add to existing project
            #Open a directory opening box starting at the directory where audio files are stored
            DIR_PATH = g.diropenbox(msg = "Select a project directory", default = AUDIO_DIRECTORY)
        
        #Count number of existing attempts
        loss_file_path = DIR_PATH + "/" + ATTEMPT_FILE_NAME
        num_files = max(len(os.listdir(DIR_PATH)) - 1,0) #don't count the file of attempt records
        #This will be the file name the user's attempt will be saved in
        filename = DIR_PATH + "/file" + str(num_files) + ".wav"


        #Prompt user to begin recording
        record_msg = "Click to start recording.\n" + \
                    "Press Control-C while in the command line application to stop recording\n" + \
                    ("Otherwise, recording will stop after %d seconds." % record_audio.RECORD_SECONDS)
        g.msgbox(record_msg, ok_button = "Begin Recording")
    except Exception as e:
        print "Could not create GUI", e
        #Fall back to command line interface
        enter = raw_input("Press Enter to record...")

    print "Recording audio..."
    record_audio.record(filename)
    print "recorded audio"

#Allow user to analyze an existing file
if len(sys.argv) >= 2:
    filename = sys.argv[1]

downsample = 1
samplerate = 44100 // downsample
if len( sys.argv ) > 2: samplerate = int(sys.argv[2])

win_s = 4096 // downsample # fft size
hop_s = 512  // downsample # hop size

s = source(filename, samplerate, hop_s)
samplerate = s.samplerate

tolerance = 0.8

#Create low-pass filter: https://tomroelandts.com/articles/how-to-create-a-simple-low-pass-filter
#Assume most users won't sing above 1200 Hz or so, which is A6 (very high soprano)
fc = 0.03  # Cutoff frequency as a fraction of the sampling rate (in (0, 0.5)).

b = 0.08  # Transition band, as a fraction of the sampling rate (in (0, 0.5)).
N = int(np.ceil((4 / b)))
if not N % 2: N += 1  # Make sure that N is odd.
n = np.arange(N)
 
# Compute sinc filter.
h = np.sinc(2 * fc * (n - (N - 1) / 2.))
 
# Compute Blackman window.
w = np.blackman(N)
 
# Multiply sinc filter with window.
h = h * w
 
# Normalize to get unity gain.
h = h / np.sum(h)

pitch_method = "yinfft"
pitch_o = pitch(pitch_method, win_s, hop_s, samplerate)
pitch_o.set_unit("hertz")
pitch_o.set_tolerance(tolerance)

pitches = []
confidences = []

# total number of frames read
total_frames = 0
while True:
    samples, read = s() #read a given number of samples at a time
    #Apply low pass filter
    samples = np.convolve(samples, h, mode="same").astype(np.float32)

    #Perform pitch detection and save confidence in case we want it
    pitch = pitch_o(samples)[0]
    confidence = pitch_o.get_confidence()
    pitches += [pitch]
    confidences += [confidence]
    total_frames += read
    if read < hop_s: break

#Calculate optimal tuning
samples = pitches

#Set this to True if we want to solve the optimization problem with fancy math
#But the problem is small enough that brute force is actually faster
use_annealing = False

tuning_optimization_result = calculate_tuning.optimize_loss(samples, use_annealing)
if use_annealing:
    tuning_param = tuning_optimization_result.x
    tuning = tuning_param * 2**(69.0/12) #calculate frequency of A4 at this tuning
    tuning_loss = tuning_optimization_result.fun
else:
    tuning_loss, tuning, tuning_param = tuning_optimization_result

#Display results (best tuning and how good (or more precisely how bad) it was)
print("Best tuning A%d has loss %f" % (tuning, tuning_loss))
g.msgbox(("Most likely tuning is A%d, with a total squared deviation of %f")%(tuning, tuning_loss))

#Write the results of this attempt (tuning and loss) to a file
#This way, the user can compare how they've done on successive attempts

#In the future, we might want to try more sophisticated pattern recognition
#To combine the attempts to figure out what the intended note sequence was
#Or study the user's attempts in more detail to see consistent problem spots
loss_file = open(loss_file_path, "a")
loss_file.write("A" + str(tuning) + " " + str(tuning_loss) + "\n")
loss_file.close()

#Calculate deviations from what we take to be the intended tuning and plot them
deviations = list()
predicted_pitches = list()
for actual_pitch in samples:
    predicted_pitch = calculate_tuning.calculate_predicted_pitch(actual_pitch, tuning_param)
    predicted_pitches += [predicted_pitch]
    pitch_deviation = actual_pitch - predicted_pitch
    deviations += [pitch_deviation]

#Only consider nonzero pitches (zero pitches mean no sound: nothing was played)
predicted = np.asarray(predicted_pitches)
actual = np.asarray(samples)
nonzero_predicted_indices = np.nonzero(predicted)[0]
nonzero_actual_indices = np.nonzero(actual)[0]
nonzero_predicted = predicted[nonzero_predicted_indices]
nonzero_actual = actual[nonzero_actual_indices]

#Plot deviations (sharpness or flatness compared to the intended tuning) in Hz
deviations = np.asarray(deviations)
plt.plot(nonzero_actual_indices, deviations[nonzero_actual_indices])
plt.legend(["deviations"], loc = "upper left")
plt.figure()

#Plot predicted frequencies versus actual frequencies
#In the future could try more sophisticated techniques to transcribe an actual musical score
#This would involve fancy methods like onset detection, quantization, etc. 
plt.plot(nonzero_predicted_indices, nonzero_predicted)
plt.plot(nonzero_actual_indices, nonzero_actual)
plt.legend(["predicted pitches", "actual pitches"], loc = "upper left")
plt.show()