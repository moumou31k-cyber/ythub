from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp, os, tempfile, threading

app = Flask(__name__)

@app.route('/info', methods=['POST'])
def info():
    url = request.json.get('url','')
    try:
        with yt_dlp.YoutubeDL({'quiet':True}) as ydl:
            meta = ydl.extract_info(url, download=False)
        return jsonify({'title': meta.get('title',''), 'duration': meta.get('duration_string',''), 'thumbnail': meta.get('thumbnail','')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url','')
    quality = request.json.get('quality','720')
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, '%(title)s.%(ext)s')
    fmt = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best[ext=mp4]/best'
    opts = {'format': fmt, 'outtmpl': out, 'quiet': True, 'merge_output_format': 'mp4'}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url)
            fname = ydl.prepare_filename(info).replace('.webm','.mp4').replace('.mkv','.mp4')
            # find actual file
            for f in os.listdir(tmp):
                if f.endswith('.mp4'):
                    fname = os.path.join(tmp, f)
                    break
        @after_this_request
        def cleanup(response):
            def _del():
                try: os.remove(fname); os.rmdir(tmp)
                except: pass
            threading.Thread(target=_del).start()
            return response
        return send_file(fname, as_attachment=True, mimetype='video/mp4')
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/')
def index():
    here = os.path.dirname(os.path.abspath(__file__))
    return open(os.path.join(here, 'index.html'), encoding='utf-8').read()

if __name__ == '__main__':
    app.run(port=5000, debug=False)
