from flask import Flask, request, send_file, jsonify
import subprocess, base64, os

app = Flask(__name__)

@app.route('/')
def home():
    return "FFmpeg API is running! ✅"

@app.route('/image-to-video', methods=['POST'])
def image_to_video():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({"error": "No image provided"}), 400

        base64_image = data['image']
        duration = data.get('duration', 5)

        # Clean base64
        if ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        base64_image = base64_image.strip().replace('\n','').replace(' ','')
        missing = len(base64_image) % 4
        if missing:
            base64_image += '=' * (4 - missing)

        # Decode
        img_data = base64.b64decode(base64_image)
        
        # Log size for debugging
        print(f"Image bytes received: {len(img_data)}")

        if len(img_data) < 100:
            return jsonify({
                "error": "Image data too small",
                "bytes": len(img_data)
            }), 400

        # Save image
        img_path = '/tmp/input.jpg'
        output_path = '/tmp/output.mp4'

        with open(img_path, 'wb') as f:
            f.write(img_data)

        print(f"Saved image: {os.path.getsize(img_path)} bytes")

        # FFmpeg convert
        result = subprocess.run([
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', img_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
            output_path
        ], capture_output=True, text=True, timeout=120)

        print(f"FFmpeg stderr: {result.stderr[-300:]}")

        if not os.path.exists(output_path):
            return jsonify({
                "error": "FFmpeg failed",
                "stderr": result.stderr[-300:]
            }), 500

        video_size = os.path.getsize(output_path)
        print(f"Output video: {video_size} bytes")

        if video_size < 1000:
            return jsonify({
                "error": "Video too small",
                "size": video_size,
                "stderr": result.stderr[-300:]
            }), 500

        return send_file(
            output_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name='reel.mp4'
        )

    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
