import board,busio, io 
import adafruit_mlx90640
import numpy as np
from flask import Flask, jsonify, render_template_string
from picamera2 import Picamera2
import base64
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


app = Flask(__name__)

#Sets up the thermal camera
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) #Sets up i2c to work
mlx = adafruit_mlx90640.MLX90640(i2c) #Defines mlx
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_1_HZ #Sets the refresh rate of the camera.
x_pixels = 32 #Thermal camera resolution X
y_pixels = 24 #Thermal camera resolution Y

def get_image():
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)

    picam2.start()

    theImage = picam2.capture_image()

    with io.BytesIO() as buffer:
        theImage.save(buffer, format="PNG")
        theImageBytes = buffer.getvalue()

    theImageBase64 = base64.b64encode(theImageBytes).decode('utf-8')
    
    picam2.stop()
    picam2.close()

    return theImageBase64

def get_thermal():
        frame = np.zeros(x_pixels*y_pixels) #Creates frame array. 
        rounded_frame = np.zeros(x_pixels*y_pixels) #Creates frame array. 
        mlx.getFrame(frame) #Gets the temperature information from the camera and enters it into the frame array
        rounded_frame = np.round(frame, 2)
        return rounded_frame

def get_heatmap():
    # Reshape the input array based on the X and Y supplied (set above)
    matrix = np.reshape(get_thermal(), (y_pixels, x_pixels))

    # Define the color map with a linear gradient
    colors = [(0, 'blue'), (0.25, 'green'), (0.5, 'yellow'), (0.75, 'orange'), (1, 'red')]
    cmap = LinearSegmentedColormap.from_list('temperature', colors)

    # Calculate the size of the heatmap in pixels
    block_size = 10
    heatmap_width = matrix.shape[1] * block_size
    heatmap_height = matrix.shape[0] * block_size

    aspect_ratio = matrix.shape[0] / matrix.shape[1] # Calculate the aspect ratio of the matrix
    fig, ax = plt.subplots(figsize=(x_pixels, y_pixels * aspect_ratio)) # Set the figsize to ensure square color blocks
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', extent=[0, heatmap_width, 0, heatmap_height], origin='lower')# Create a rotated heatmap without normalizing matrix values
    ax.axis('off') # Remove axis labels and ticks
    cbar = plt.colorbar(im, ax=ax) # Add color bar

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    plt.close()

    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    return img_base64

@app.route("/")
def index():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Thermal Detector and Documentor</title>
    </head>
    <body>
        Returns a JSON response<br>
        Use <a href="/thermal">/thermal</a> for an array of temperatures and the aspect ratio of the array values/thermal sensor<br>
        Use <a href="/photo">/photo</a> for a base64 encoded photo from the camera<br>
        Use <a href="/heatmap">/heatmap</a> for a base64 encoded heatmap from the thermal camera<br>
        Use <a href="/view">/view</a> to show heatmap and photo in browser (very slow)<br>
        <br>
        Typical usage:<br>
        1. Use /view to set up and identify points of interest for the temperature sensor<br>
        2. Use /thermal to regularly check for temperatures of interest<br>
        3. When triggered (by step 2) get /heatmap and /photo to document the event<br>
        <br>

    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/thermal')
def thermal():
        return jsonify({"temperatures": get_thermal().tolist(), "x_pixels": x_pixels, "y_pixels": y_pixels})

@app.route('/photo')
def photo():
    return jsonify({"image": get_image()})

@app.route('/heatmap')
def heatmap():
    return jsonify({"image": get_heatmap()})

@app.route('/view')
def view():
    heat64 = get_heatmap()
    img64 = get_image()
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Images</title>
    </head>
    <body>
        <img src="data:image/png;base64,{heat64}" alt="Image" style="width: 100%;">
        <img src="data:image/png;base64,{img64}" alt="Image" style="width: 100%;">
    </body>
    </html>
    """
    return render_template_string(html_content)



if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0') #Enables debug and sets host
