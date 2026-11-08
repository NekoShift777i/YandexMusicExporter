import re

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from auth import connect


def escape_markdown(text: str) -> str:
    """Защищает названия от разметки Markdown и Obsidian."""

    text = str(text)

    # Разделяем строку по последовательностям процентов.
    parts = re.split(r"(%{2,})", text)
    result = []

    for part in parts:
        if not part:
            continue

        # Комментарии Obsidian защищаем встроенным кодом.
        if re.fullmatch(r"%{2,}", part):
            result.append(f"`{part}`")
            continue

        # Экранируем обратную косую черту и апострофы кода.
        part = part.replace("\\", "\\\\")
        part = part.replace("`", "\\`")

        # Экранируем символы форматирования.
        part = re.sub(r"([*_~\[\]])", r"\\\1", part)

        # Защищаем решётку и восклицательный знак.
        part = re.sub(r"([#!])", r"\\\1", part)

        # Защищаем HTML-подобные конструкции.
        part = part.replace("&", "&amp;")
        part = part.replace("<", "&lt;")
        part = part.replace(">", "&gt;")

        result.append(part)

    return "".join(result)


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

    # Получаем композиции порциями.
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
                for artist in (track.artists or [])
                if artist.name
            ) or "Неизвестный исполнитель"

            # Сохраняем ID для устойчивой нумерации совпадений.
            grouped[artists].append((title, int(track.id)))
            total += 1

    lines = [
        "# Любимые песни",
        "",
        f"Всего композиций: {total}",
        f"Последнее обновление: {datetime.now():%d.%m.%Y %H:%M}",
        "",
    ]

    for artist in sorted(grouped, key=str.casefold):
        entries = grouped[artist]
        counts = Counter(title.casefold() for title, _ in entries)
        variants = defaultdict(int)
        titled_entries = []

        # ID задаёт постоянный порядок вариантов внутри каждой группы.
        for title, track_id in sorted(entries, key=lambda item: item[1]):
            if counts[title.casefold()] > 1:
                variants[title.casefold()] += 1
                title += f" (Вариант {variants[title.casefold()]})"
            titled_entries.append(title)

        lines.append(f"## {escape_markdown(artist)}")
        lines.append("")

        for title in sorted(titled_entries, key=str.casefold):
            lines.append(f"- {escape_markdown(title)}")

        lines.append("")

    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    return total, len(grouped)
