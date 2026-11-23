import re
import sys
import subprocess
from pathlib import Path

FFMPEG = Path(r"E:\cs2\videos\ffmpeg\bin\ffmpeg.exe")
SAMPLE_FPS = 1  # Même valeur que dans le script d'extraction


def get_video():
    if len(sys.argv) < 2:
        raise ValueError("Aucune vidéo reçue depuis le BAT.")

    video = Path(sys.argv[1]).resolve()

    if not video.is_file():
        raise FileNotFoundError(f"Vidéo introuvable : {video}")

    return video


def read_logs(video):
    logs_file = (
        Path(r"E:\cs2\videos\cut")
        / video.stem
        / "logs"
        / "shop_death_detection.txt"
    )

    if not logs_file.is_file():
        raise FileNotFoundError(f"Logs introuvables : {logs_file}")

    frame_pattern = re.compile(
        r"SHOP:\s*f_(\d+)\s*->\s*(SHOP|DEATH):\s*f_(\d+)",
        re.IGNORECASE,
    )

    segments = []

    with logs_file.open("r", encoding="utf-8") as file:
        for line in file:
            match = frame_pattern.search(line)

            if not match:
                continue

            start_frame = int(match.group(1))
            event_type = match.group(2).upper()
            end_frame = int(match.group(3))

            if end_frame <= start_frame:
                continue

            start_time = (start_frame - 1) / SAMPLE_FPS
            end_time = (end_frame - 1) / SAMPLE_FPS

            segments.append((start_time, end_time))

            print(
                f"Segment détecté : "
                f"f_{start_frame:06d} -> "
                f"{event_type}: f_{end_frame:06d} "
                f"({start_time:.2f}s -> {end_time:.2f}s)"
            )

    if not segments:
        raise ValueError(
            "Aucun segment valide trouvé dans les logs."
        )

    return segments


def cut_video(video, segments):
    output_dir = (
        Path(r"E:\cs2\videos\cut")
        / video.stem
        / "clips"
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    for index, (start_time, end_time) in enumerate(segments, start=1):
        duration = end_time - start_time

        if duration <= 0:
            continue

        output_file = output_dir / f"clip_{index:03d}.mp4"

        print(f"\nClip {index}/{len(segments)}")
        print(f"Début : {start_time:.2f}s")
        print(f"Fin   : {end_time:.2f}s")
        print(f"Durée : {duration:.2f}s")

        result = subprocess.run(
            [
                str(FFMPEG),
                "-y",
                "-ss", str(start_time),
                "-i", str(video),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-c:a", "aac",
                "-movflags", "+faststart",
                str(output_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
        )

        if result.returncode:
            raise RuntimeError(
                f"Échec FFmpeg sur {output_file.name} :\n"
                f"{result.stderr.strip()}"
            )

    print(
        f"\nTerminé ! {len(segments)} clips enregistrés dans : "
        f"{output_dir}"
    )


def main():
    video = get_video()
    print(f"Vidéo : {video.name}")

    segments = read_logs(video)
    print(f"\n{len(segments)} segments trouvés dans les logs.")

    cut_video(video, segments)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nERREUR : {error}")
        sys.exit(1)
