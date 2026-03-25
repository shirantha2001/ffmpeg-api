from flask import Flask, request, send_file
import subprocess, base64, os, tempfile

app = Flask(__name__)

@app.route('/image-to-video', methods=['POST'])
def image_to_video():
    data = request.json
    base64_image = data['image']
    duration = data.get('duration', 5)

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as img_file:
        img_file.write(base64.b64decode(base64_image))
        img_path = img_file.name

    output_path = img_path.replace('.jpg', '.mp4')

    subprocess.run([
        'ffmpeg', '-loop', '1',
        '-i', img_path,
        '-c:v', 'libx264',
        '-t', str(duration),
        '-pix_fmt', 'yuv420p',
        '-vf', 'scale=1080:1920',
        '-y', output_path
    ])

    return send_file(output_path, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))