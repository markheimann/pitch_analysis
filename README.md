# pitch_analysis

Dependencies:
- easygui (for GUI)
- Matplotlib (for making plots)
- NumPy, SciPy (for general scientific computing)
- PyAudio (for audio handling, i.e. recording)
- Aubio (for audio analysis e.g. pitch detection)

Usage:
- Run detect_pitch.py ("python detect_pitch.py")
- Select one of two options:
- Create new project: enter a new project name (cannot be name of existing project)
  - Directory will be made with the project's name
  - Can add attempts to the directory, with name file0, file1, file2, etc.
  - Results of attempts saved to a file called attempt_info.txt
- Add another attempt to existing project (will be prompted to select a project directory
- Begin recording (can record up to 10 seconds of audio)
- Stop recording before 10 seconds by hitting Control-C (must be in the terminal or command line)
- Graphs will automatically be generated, and results (tuning and loss) saved in attempt_info.txt


