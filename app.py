import board,busio
import adafruit_mlx90640
import numpy as np
from flask import Flask, jsonify
from picamera2 import Picamera2
import base64

app = Flask(__name__)

#Sets up the thermal camera
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000) #Sets up i2c to work
mlx = adafruit_mlx90640.MLX90640(i2c) #Defines mlx
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_1_HZ #Sets the refresh rate of the camera.
x_pixels = 32 #Thermal camera resolution X
y_pixels = 24 #Thermal camera resolution Y

@app.route("/")
def index():
    return "Returns a JSON resonse<br>Use /thermal for an array of temperatures <br>Use /capture for a base64 encoded image"

@app.route('/thermal')

def thermal():
        frame = np.zeros(x_pixels*y_pixels) #Creates frame array. 
        mlx.getFrame(frame) #Gets the temperature information from the camera and enters it into the frame array
        frameString = ','.join(str(x) for x in frame) #Converts frame into a , seperated string
        ##return frameString #Returns the captured temperature of the camera's pixels as a , seperated string
        return jsonify({"temperatures": frame.tolist()})

@app.route('/capture')
def capture():
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)

    picam2.start()

    theImage = picam2.capture_image()
    theImageBytes = theImage.tobytes()
    theImageBase64 = base64.b64encode(theImageBytes).decode('utf-8')
    
    picam2.stop()
    picam2.close()

    return jsonify({"image": theImageBase64})

if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0') #Enables debug and sets host
