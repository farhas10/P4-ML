# Project 4: Machine Learning

Solution code for [Robotics 102 Project 4: Machine Learning (Part 3: Robot Tour Guide)](https://robotics102.github.io/projects/a4.html#tour_guide).

## Setup

Install the dependencies using:
```bash
pip install -r requirements.txt
```

## Testing

Test the camera to see it take pictures and store in the `output` folder
```bash
python ./utils/camera_test.py 
```

**Test the classifier**:
1. Use `camera_test.py` to take a photo of a poster 
2. Make sure in the `output` folder `08_bordered_frame_0.jpg` actually shows a binary image of the poster
3. Upload your trained model under the main folder
4. Edit `PATH_TO_MODEL` in both `robot_tour_guide.py` and `utils/classifier_test.py`
5. Run `utils/classifier_test.py` and check the printed output
```bash
python ./utils/classifier_test.py
```
You should able to see `"Detect {some number}"` in the terminal.

## Setting the Waypoints and Labels

Run the `waypoint_writer.py` script while localized to store the waypoints and labels for your current map in waypoints.txt. They will be automatically loaded in `robot_tour_guide.py`. Drive using the webapp and respond to the prompts from the script. Take photos from your current position to check if the nearest poster is visible. Record these waypoints with appropriate labels.

```bash
python ./waypoint_writer.py
```

Alternatively, you can hard code your waypoints and labels directly.

## Running the Program

```bash 
python ./robot_tour_guide.py
```
