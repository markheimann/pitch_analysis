import numpy as np
import scipy.optimize

SEMITONE_RATIO = 2**(1.0/12) #constant 
LOW_A4 = 428 #anything lower will probably sound more like Ab
HIGH_A4 = 454 #anything higher will probably sound more like Bb
A4_MIDI_NUMBER = 69 #A4, or concert A, in MIDI note numbering scheme

#Calculate the loss of a sequence of pitches
#if additionally given the tuning parameter that says what the tuning should have been
def pitch_loss(tuning_param, actual_pitches):
  loss = 0
  ##make sure tuning parameter is nonnegative
  if tuning_param < 7.69268353 or tuning_param > 8.1757898156: return np.inf
  for pitch in actual_pitches: #should probably vectorize this
    if pitch > 0: #otherwise no sound, so skip this
      predicted_pitch = calculate_predicted_pitch(pitch, tuning_param)
      pitch_deviation = (predicted_pitch - pitch)**2 #calculate squared loss for individual note
      loss += pitch_deviation
  print "loss: ", loss
  return loss

#Calculate what was probably the intended pitch given an actual pitch and the tuning
def calculate_predicted_pitch(actual_pitch, tuning_param):
  if actual_pitch <= 0.01: return 0 #i.e. not a note (0.01 to avoid rounding error)
  predicted_x = (np.log(actual_pitch) - np.log(tuning_param)) / np.log(SEMITONE_RATIO)
  predicted_note = int(round(predicted_x))
  predicted_pitch = tuning_param * SEMITONE_RATIO**predicted_note
  return predicted_pitch

#Calculate the tuning by trying all possible tunings and seeing which one has lowest loss
def calculate_tuning_brute_force(actual_pitches):
  min_loss = np.inf
  min_Afreq = 0
  min_tuning_param = 0
  for A in range(LOW_A4, HIGH_A4): #choices of frequency of A4
    #calculate tuning parameter for given tuning
    tuning_param = A / SEMITONE_RATIO**A4_MIDI_NUMBER

    #calculate predicted pitches based on tuning parameter
    predicted_pitches = []
    for pitch in actual_pitches: 
      if pitch > 0:
        predicted_pitches += [calculate_predicted_pitch(pitch, tuning_param)]
      else:
        predicted_pitches += [0] #just assume we can predict the no sound case correctly

    #calculate loss based on predicted pitches
    squared_differences = (np.asarray(predicted_pitches) - np.asarray(actual_pitches))**2
    loss = np.sum(squared_differences)

    #update minimum loss if found new minimum
    if loss < min_loss:
      min_loss = loss
      min_Afreq = A
      min_tuning_param = tuning_param
  return (min_loss, min_Afreq, min_tuning_param)



def optimize_loss(pitches, use_annealing):
  if use_annealing:
    return scipy.optimize.basinhopping(pitch_loss, [8.0], minimizer_kwargs = {"args" : (pitches,)}, niter = 10)
  else:
    return calculate_tuning_brute_force(pitches)
