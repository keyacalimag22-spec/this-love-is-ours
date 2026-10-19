from flask import (
    Flask, request, redirect, url_for,
    render_template_string, send_from_directory
)
from pathlib import Path
from werkzeug.utils import secure_filename
import json
import uuid

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# -------------------------------
# FOLDERS AND SETTINGS
# -------------------------------

BASE_FOLDER = Path(__file__).parent
FOLDER = BASE_FOLDER
DATA = FOLDER / "gallery.json"

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_TYPES = {".mp4", ".webm", ".mov"}
AUDIO_TYPES = {".mp3", ".wav", ".ogg", ".m4a"}

ALLOWED_TYPES = IMAGE_TYPES | VIDEO_TYPES | AUDIO_TYPES


def load_items():
    if DATA.exists():
        try:
            with open(DATA, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_items(items):
    with open(DATA, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=4, ensure_ascii=False)


# -------------------------------
# WEBSITE HTML AND CSS
# -------------------------------

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>This Love Is Ours | Lancesot and Keya</title>

    <style>
        * {
            box-sizing: border-box;
        }

        html {
            scroll-behavior: smooth;
            scroll-padding-top: 120px;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            color: white;
            background-color: #24152e;
            background-image:
                linear-gradient(
                    rgba(20, 10, 35, 0.70),
                    rgba(20, 10, 35, 0.82)
                ),
                url("/files/1000043580.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            overflow-x: hidden;
        }

        /* NAVIGATION */

        header {
            background: rgba(22, 13, 35, 0.97);
            padding: 18px 12px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        header h2 {
            color: #ffb9dc;
            margin: 0 0 14px;
        }

        nav {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px;
        }

        nav a {
            color: #f7c7ff;
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 20px;
            transition: 0.3s;
        }

        nav a:hover {
            background: #d65ca9;
            color: white;
        }

        /* HOME */

        .hero {
            text-align: center;
            padding: 100px 20px;
            background: rgba(80, 35, 100, 0.30);
            animation: fadeIn 1s ease;
        }

        .hero h1 {
            font-size: clamp(32px, 5vw, 55px);
            color: #fff0fa;
            text-shadow: 0 0 15px #d65ca9;
            animation: glow 2s infinite alternate;
        }

        .hero p {
            font-size: 18px;
            line-height: 1.8;
        }

        /* FEATURED PHOTO */

        .featured-photo {
            max-width: 900px;
            margin: 30px auto;
            padding: 0 18px;
            text-align: center;
        }

        .featured-photo a {
            display: block;
            cursor: zoom-in;
            overflow: hidden;
            border-radius: 18px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }

        .featured-photo img {
            display: block;
            width: 100%;
            max-height: 500px;
            object-fit: cover;
            transition: 0.3s;
        }

        .featured-photo a:hover img {
            transform: scale(1.03);
            filter: brightness(1.1);
        }

        .featured-caption {
            color: #ffd5ed;
            font-size: 14px;
        }

        /* GENERAL SECTIONS */

        section {
            max-width: 1100px;
            margin: 25px auto;
            padding: 28px;
            background: rgba(28, 17, 42, 0.91);
            border-radius: 18px;
            box-shadow: 0 5px 25px rgba(0, 0, 0, 0.2);
            animation: fadeIn 0.8s ease;
        }

        h2 {
            color: #ffb9dc;
        }

        p {
            line-height: 1.7;
            overflow-wrap: anywhere;
        }

        /* GALLERIES */

        .gallery {
            display: grid;
            grid-template-columns: repeat(
                auto-fit, minmax(220px, 1fr)
            );
            gap: 20px;
        }

        .card {
            background: rgba(255, 255, 255, 0.09);
            padding: 14px;
            border-radius: 14px;
            overflow: hidden;
            transition: transform 0.3s;
        }

        .card:hover {
            transform: translateY(-4px);
        }

        .card img,
        .card video {
            display: block;
            width: 100%;
            max-height: 350px;
            object-fit: cover;
            border-radius: 10px;
        }

        .card h3 {
            color: #ffd5ed;
            overflow-wrap: anywhere;
        }

        .media-click {
            display: block;
            cursor: zoom-in;
            overflow: hidden;
            border-radius: 10px;
        }

        .media-click img {
            transition: transform 0.3s, filter 0.3s;
        }

        .media-click:hover img {
            transform: scale(1.04);
            filter: brightness(1.1);
        }

        .gallery-video {
            cursor: zoom-in;
        }

        /* FULL-SCREEN PHOTO AND VIDEO VIEWER */

        .media-modal {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 9999;
            background: rgba(10, 4, 18, 0.96);
            align-items: center;
            justify-content: center;
            padding: 60px 15px 20px;
        }

        .media-modal.open {
            display: flex;
        }

        .media-modal-content {
            max-width: 95vw;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }

        .media-modal-content img,
        .media-modal-content video {
            display: block;
            max-width: 95vw;
            max-height: 78vh;
            width: auto;
            height: auto;
            object-fit: contain;
            border-radius: 10px;
        }

        .media-modal-title {
            color: #ffd5ed;
            text-align: center;
            font-size: 18px;
        }

        .media-modal-close {
            position: absolute;
            top: 12px;
            right: 20px;
            color: white;
            background: #d63384;
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            font-size: 28px;
            cursor: pointer;
        }

        /* MUSIC PLAYER */

        .music-box {
            max-width: 650px;
            margin: 20px auto;
            padding: 25px;
            text-align: center;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 15px;
        }

        .music-icon {
            font-size: 48px;
            animation: musicFloat 2s infinite ease-in-out;
        }

        audio {
            width: 100%;
            max-width: 450px;
            margin: 10px 0;
        }

        .small {
            font-size: 13px;
            color: #e8d5e8;
        }

        /* UPLOAD FORM */

        form {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        label {
            color: #ffd5ed;
            font-weight: bold;
        }

        input,
        textarea,
        button {
            font: inherit;
            padding: 12px;
            border-radius: 9px;
        }

        input,
        textarea {
            border: 1px solid #e7b8df;
            background: #fffaff;
            color: #2c1730;
            width: 100%;
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        button {
            border: none;
            background: #d65ca9;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }

        button:hover {
            background: #b83d8c;
        }

        .message {
            padding: 12px;
            background: rgba(214, 92, 169, 0.22);
            border-radius: 10px;
            margin-bottom: 15px;
        }        

        /* FOOTER */

        footer {
            background: rgba(22, 13, 35, 0.97);
            text-align: center;
            padding: 25px 12px;
            color: #ffd5ed;
            margin-top: 35px;
        }

        /* ANIMATIONS */

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(15px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes glow {
            from {
                text-shadow: 0 0 8px #d65ca9;
            }

            to {
                text-shadow: 0 0 25px #ff69b4;
            }
        }

        @keyframes musicFloat {
            0%, 100% {
                transform: translateY(0);
            }

            50% {
                transform: translateY(-8px);
            }
        }

        /* PHONE LAYOUT */

        @media (max-width: 600px) {
            body {
                background-attachment: scroll;
            }

            header {
                padding: 14px 8px;
            }

            header h2 {
                font-size: 21px;
            }

            nav {
                gap: 3px;
            }

            nav a {
                font-size: 13px;
                padding: 8px;
            }

            .hero {
                padding: 65px 14px;
            }

            .hero h1 {
                font-size: 30px;
            }

            .hero p {
                font-size: 16px;
            }

            section {
                margin: 14px 10px;
                padding: 18px 14px;
            }

            .featured-photo {
                padding: 0 12px;
            }

            .gallery {
                grid-template-columns: 1fr;
            }

            .card img,
            .card video {
                max-height: 420px;
            }

            .media-modal-content img,
            .media-modal-content video {
                max-height: 70vh;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
            }
        }
    </style>
</head>

<body>

<header>
    <h2>This Love Is Ours</h2>

    <nav>
        <a href="#home">Home</a>
        <a href="#about">About</a>
        <a href="#photos">Photos</a>
        <a href="#videos">Videos</a>
        <a href="#music">Music</a>
        <a href="#upload">Upload</a>
    </nav>
</header>

<!-- HOME -->

<div id="home" class="hero">
    <h1>Lancesot and Keya! &lt;3</h1>

    <p>SOBRADO.</p>

    <p>Photography | Videos | Music | Memories</p>

    <p>
        Every picture holds a memory, and every memory
        is part of our story. 
    </p>
</div>

<!-- FEATURED PHOTO ABOVE ABOUT US -->

<div class="featured-photo">
    <a
        class="media-click"
        href="{{ url_for('uploaded_file', filename='1000043577.jpg') }}"
        data-title="Our Special Memory"
        data-type="image"
    >
        <img
            src="{{ url_for('uploaded_file', filename='1000043577.jpg') }}"
            alt="Our special memory"
        >
    </a>

    <p class="featured-caption">
         💗
        
    </p>
</div>

<!-- ABOUT US -->

<section id="about">
    <h2>💌 About Us</h2>

    <p>
        Welcome to our personal life! We enjoy taking pictures,
        creating memories, making videos, and listening to music.
        This website is our little space to keep our favorite moments
        together in one place.
    </p>

    <p>
        Every day gives us another memory to treasure.
        Thank you for visiting our little corner of the internet. 💗
    </p>
</section>

<!-- PHOTOS -->

<section id="photos">
    <h2>📸 Our Photos</h2>

    {% set images = items | selectattr("kind", "equalto", "image") | list %}

    {% if images %}
    <div class="gallery">
        {% for item in images %}
        <div class="card">

            <a
                class="media-click"
                href="{{ url_for('uploaded_file', filename=item.filename) }}"
                data-title="{{ item.title }}"
                data-type="image"
            >
                <img
                    src="{{ url_for('uploaded_file', filename=item.filename) }}"
                    alt="{{ item.title }}"
                    loading="lazy"
                >
            </a>

            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>

            <p class="small">♥</p>

        </div>
        {% endfor %}
    </div>
    {% else %}
    <p>No photos yet. Upload your favorite pictures below! 💗</p>
    {% endif %}
</section>

<!-- VIDEOS -->

<section id="videos">
    <h2>🎬 Our Videos</h2>

    {% set videos = items | selectattr("kind", "equalto", "video") | list %}

    {% if videos %}
    <div class="gallery">
        {% for item in videos %}
        <div class="card">

            <video
                class="gallery-video"
                controls
                preload="metadata"
                playsinline
                data-title="{{ item.title }}"
            >
                <source
                    src="{{ url_for('uploaded_file', filename=item.filename) }}"
                >
                Your browser does not support video playback.
            </video>

            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>

            <p class="small">
                Click the video!.
            </p>

        </div>
        {% endfor %}
    </div>
    {% else %}
    <p>No videos uploaded yet. Add a favorite memory! 🎥</p>
    {% endif %}
</section>

<!-- MUSIC -->

<section id="music">
    <h2>🎵 Our Music</h2>

    <div class="music-box">
        <div class="music-icon">🎶</div>

        <h3>Our Song</h3>

        <p>
            Listen to our favorite song while looking at our memories. 
        </p>

        <audio controls loop preload="metadata">
            <source
                src="{{ url_for('uploaded_file', filename='background-music.mp3') }}"
                type="audio/mpeg"
            >
            Your browser does not support audio playback.
        </audio>

        <p class="small">
            Press Play to start the music. 
        </p>
    </div>

    {% set audios = items | selectattr("kind", "equalto", "audio") | list %}

    {% if audios %}
    <h3>More Songs 🎧</h3>

    <div class="gallery">
        {% for item in audios %}
        <div class="card">

            <h3>{{ item.title }}</h3>

            <audio controls preload="metadata">
                <source
                    src="{{ url_for('uploaded_file', filename=item.filename) }}"
                >
                Your browser does not support audio playback.
            </audio>

            <p>{{ item.description }}</p>

        </div>
        {% endfor %}
    </div>
    {% endif %}
</section>

<!-- UPLOAD -->

<section id="upload">
    <h2>📤 Add a Memory</h2>

    <p>
        Upload a photo, video, or audio file to add it to your website.
    </p>

    {% if message %}
    <div class="message">{{ message }}</div>
    {% endif %}

    <form
        action="{{ url_for('upload') }}"
        method="POST"
        enctype="multipart/form-data"
    >
        <label for="title">Title of our memory</label>

        <input
            id="title"
            type="text"
            name="title"
            maxlength="100"
            placeholder="Title daw"
        >

        <label for="description">Description</label>

        <textarea
            id="description"
            name="description"
            maxlength="1000"
            placeholder="Something about this memory... ah eh ah eh"
        ></textarea>

        <label for="file">Choose a photo, video, or audio file</label>

        <input
            id="file"
            type="file"
            name="file"
            accept=".jpg,.jpeg,.png,.gif,.webp,.mp4,.webm,.mov,.mp3,.wav,.ogg,.m4a"
            required
        >

        <button type="submit">Upload Our Memory ♥</button>
    </form>

    <p class="small">
        Maximum upload size: 50 MB per file.
    </p>
</section>

<footer>
    <p>Made by Lancesot and Keya ♥ </p>
    <p>Our memories, our music, our story.</p>
</footer>

<!-- FULL-SCREEN MEDIA VIEWER -->

<div class="media-modal" id="mediaModal" aria-hidden="true">

    <button
        class="media-modal-close"
        id="mediaModalClose"
        type="button"
        aria-label="Close viewer"
    >
        &times;
    </button>

    <div class="media-modal-content" id="mediaModalContent"></div>

</div>

<!-- JAVASCRIPT -->

<script>
(function () {
    const modal = document.getElementById("mediaModal");
    const content = document.getElementById("mediaModalContent");
    const closeButton = document.getElementById("mediaModalClose");

    function openViewer(src, type, title) {
        content.replaceChildren();

        const heading = document.createElement("div");
        heading.className = "media-modal-title";
        heading.textContent = title || "Our Memory";

        content.appendChild(heading);

        let media;

        if (type === "video") {
            media = document.createElement("video");
            media.controls = true;
            media.autoplay = true;
            media.playsInline = true;
            media.src = src;
        } else {
            media = document.createElement("img");
            media.src = src;
            media.alt = title || "Full-size photo";
        }

        content.appendChild(media);

        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
    }

    function closeViewer() {
        const video = content.querySelector("video");

        if (video) {
            video.pause();
            video.removeAttribute("src");
            video.load();
        }

        content.replaceChildren();
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
    }

    // Click any photo, including the featured photo.
    document.querySelectorAll(".media-click").forEach(function (link) {
        link.addEventListener("click", function (event) {
            event.preventDefault();

            openViewer(
                link.href,
                "image",
                link.dataset.title
            );
        });
    });

    // Click a video to open it in the larger viewer.
    document.querySelectorAll(".gallery-video").forEach(function (video) {
        video.addEventListener("click", function (event) {
            // Keep normal video controls working when clicked.
            if (event.target.closest("button")) {
                return;
            }

            const source = video.querySelector("source");
            const videoURL = source ? source.src : video.currentSrc;

            if (videoURL) {
                openViewer(
                    videoURL,
                    "video",
                    video.dataset.title || "Our Video"
                );
            }
        });
    });

    closeButton.addEventListener("click", closeViewer);

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeViewer();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeViewer();
        }
    });

})();
</script>

</body>
</html>
"""


# -------------------------------
# WEBSITE ROUTES
# -------------------------------

@app.route("/")
def home():
    items = load_items()
    message = request.args.get("message", "")

    return render_template_string(
        HTML,
        items=items,
        message=message
    )


@app.route("/files/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(FOLDER, filename)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not file or not file.filename:
        return redirect(
            url_for("home", message="Please choose a file.")
        )

    original_name = secure_filename(file.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_TYPES:
        return redirect(
            url_for("home", message="Unsupported file type.")
        )

    if extension in IMAGE_TYPES:
        kind = "image"
    elif extension in VIDEO_TYPES:
        kind = "video"
    else:
        kind = "audio"

    if not title:
        title = "Our Memory"

    filename = f"{uuid.uuid4().hex}{extension}"

    try:
        file.save(FOLDER / filename)

        items = load_items()

        items.insert(0, {
            "filename": filename,
            "title": title[:100],
            "description": description[:1000],
            "kind": kind
        })

        save_items(items)

    except OSError:
        return redirect(
            url_for("home", message="Upload failed. Please try again.")
        )

    return redirect(
        url_for("home", message="Upload successful! 💗")
    )


# -------------------------------
# START WEBSITE
# -------------------------------

if __name__ == "__main__":
    print("This Love Is Ours is starting...")
    print("Open http://127.0.0.1:5000 in your browser.")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
