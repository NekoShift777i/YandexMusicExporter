import re

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from auth import connect




def escape_markdown(text: str) -> str:
    """Точечно экранирует специальную разметку Markdown и Obsidian."""
    import re

    text = str(text)

    # Защищаем обратные косые черты.
    text = text.replace("\\", "\\\\")

    # Экранируем символы, влияющие на разметку Markdown.
    text = re.sub(r"([*_`\[\]])", r"\\\1", text)

    # Защищаем управляющие символы в начале строки.
    text = re.sub(r"^([ \t]*)([#>+-])(?=\s)", r"\1\\\2", text)

    # Защищаем комментарии Obsidian.
    text = re.sub(
        r"%{2,}",
        lambda match: f"`{match.group(0)}`",
        text
    )

    return text



def export_liked_tracks(output_path: str) -> tuple[int, int]:
    client = connect()

    likes = client.users_likes_tracks()

    if not likes or not likes.tracks:
        raise RuntimeError("Список любимых композиций пуст.")

    track_ids = [
        f"{item.id}:{item.album_id}"
        if item.album_id
        else str(item.id)
        for item in likes.tracks
    ]

    grouped = defaultdict(list)
    total = 0

    # Получаем композиции порциями
    for start in range(0, len(track_ids), 100):
        batch = track_ids[start:start + 100]
        tracks = client.tracks(batch)

        for track in tracks:
            if not track:
                continue

            title = track.title or "Без названия"

            if track.version:
                title += f" ({track.version})"

            artists = ", ".join(
                artist.name
                for artist in track.artists
                if artist.name
            ) or "Неизвестный исполнитель"

            grouped[artists].append(title)
            total += 1

    lines = [
        "# Любимые песни",
        "",
        f"Всего композиций: {total}",
        f"Последнее обновление: {datetime.now():%d.%m.%Y %H:%M}",
        "",
    ]

    for artist in sorted(grouped, key=str.casefold):
        lines.append(f"## {escape_markdown(artist)}")
        lines.append("")

        for title in sorted(grouped[artist], key=str.casefold):
            lines.append(f"- {escape_markdown(title)}")

        lines.append("")

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    return total, len(grouped)
