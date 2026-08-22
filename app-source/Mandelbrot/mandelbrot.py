import machine
import json
import neopixel
import time
from lib import st7789py
from font import vga1_8x16 as small_font
from machine import SPI, Pin, PWM, freq, reset, Timer

with open("config.json", "r") as conf:
    config = json.loads(conf.read())
    ui_color = config["ui_color"]
    bg_color = config["bg_color"]

freq(240000000)
ledPin = Pin(21)
led = neopixel.NeoPixel(ledPin, 1, bpp=3)

display = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=None,
    rotation=1,
    color_order=st7789py.BGR
    )
blight = PWM(Pin(38, Pin.OUT))
blight.freq(1000)
blight.duty_u16(40000)

# Emulate the np.linspace funtion
def linspace(start, stop, num):
    step = (stop - start) / (num - 1)
    return [start + step * i for i in range(num)]

# Determine how many iterations it takes for a point to escape.
# Returns num_iterations if it never escapes (i.e. it's in the set).
def escape_count(c, num_iterations):
    z = 0
    for i in range(num_iterations):
        z = z * z + c
        if abs(z) > 2:
            return i
    return num_iterations

# Precompute a classic smooth rainbow gradient, one color per possible
# escape-iteration count (0 .. num_iterations-1). Iteration counts
# that never escape (i.e. members of the set) are drawn in bg_color.
def build_palette(num_iterations, bg_color):
    palette = []
    for i in range(num_iterations):
        t = i / num_iterations
        r = int(9 * (1 - t) * t * t * t * 255)
        g = int(15 * (1 - t) * (1 - t) * t * t * 255)
        b = int(8.5 * (1 - t) * (1 - t) * (1 - t) * t * 255)
        palette.append(st7789py.color565(r, g, b))
    palette.append(bg_color)  # index == num_iterations -> in the set
    return palette

# Clear the display
display.fill(bg_color)

# Define the bounds and resolution.
# The real (x) range picks the classic full view of the set; the
# imaginary (y) range is derived from it to match the display's pixel
# aspect ratio (240x135), so the set renders correctly proportioned and
# fills the whole screen instead of being squashed/stretched.
width, height = 240, 135
xmin, xmax = -2.5, 1.0
y_range = (xmax - xmin) * height / width
ymin, ymax = -y_range / 2, y_range / 2
num_iterations = 32

palette = build_palette(num_iterations, bg_color)

# Generate the Mandelbrot set and plot directly to the display
re = linspace(xmin, xmax, width)
im = linspace(ymin, ymax, height)

for y, imag in enumerate(im):
    for x, real in enumerate(re):
        c = complex(real, imag)
        count = escape_count(c, num_iterations)
        display.pixel(x, y, palette[count])
            
time.sleep(10)
