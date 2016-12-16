#from https://gist.github.com/mabdrabo/8678538

import pyaudio
import wave
import easygui as g
 
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 10 #maximum number of seconds user can record
WAVE_OUTPUT_FILENAME = "file.wav"

#Record input from the computer microphone
def record(OUTPUT_FNAME):
  audio = pyaudio.PyAudio()
   
  # start recording
  stream = audio.open(format=FORMAT, channels=CHANNELS,
                  rate=RATE, input=True,
                  frames_per_buffer=CHUNK)
  frames = []
      
  #Record up to the maximum length we allow the user to record
  #Stop early if the user throws a keyboard interrupt (Control-C)
  for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    try:
      data = stream.read(CHUNK)
      frames.append(data)
    except KeyboardInterrupt: #user stops recording by hitting Control-C
      break
   
  # stop recording
  stream.stop_stream()
  stream.close()
  audio.terminate()
   
  # save recording
  waveFile = wave.open(OUTPUT_FNAME, 'wb')
  waveFile.setnchannels(CHANNELS)
  waveFile.setsampwidth(audio.get_sample_size(FORMAT))
  waveFile.setframerate(RATE)
  waveFile.writeframes(b''.join(frames))
  waveFile.close()

if __name__ == "__main__":
  enter = raw_input("Press Enter to continue...")
  record(WAVE_OUTPUT_FILENAME)