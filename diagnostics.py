
from datetime import datetime
from pathlib import Path

from auth import connect


def inspect_tracks(track_ids: list[str]) -> str:
    """Получает диагностические сведения о композициях."""

    client = connect()
    tracks = client.tracks(track_ids)

    lines = [
        "Диагностика Яндекс Музыки",
        f"Дата: {datetime.now():%d.%m.%Y %H:%M}",
        "",
    ]

    for track in tracks:
        if track is None:
            continue

        artists = ", ".join(
            artist.name
            for artist in (track.artists or [])
            if artist.name
        )

        duration = (
            f"{track.duration_ms / 1000:.3f} с"
            if track.duration_ms is not None
            else "Неизвестно"
        )

        lines.extend([
            "=" * 55,
            f"Исполнитель: {artists}",
            f"Название: {track.title}",
            f"Версия: {track.version}",
            f"ID композиции: {track.id}",
            f"Продолжительность: {duration}",
            f"Доступна: {track.available}",
        ])

        for album in track.albums or []:
            lines.extend([
                "",
                f"  Альбом: {album.title}",
                f"  ID альбома: {album.id}",
                f"  Год: {album.year}",
                f"  Дата выпуска: {album.release_date}",
                f"  Тип альбома: {getattr(album, 'type', None)}",
                f"  Издание: {getattr(album, 'version', None)}",
            ])

        lines.append("")

    return "\n".join(lines)


from collections import defaultdict


def find_duplicate_tracks() -> str:
    """Находит композиции с совпадающими названиями и исполнителями."""

    client = connect()
    likes = client.users_likes_tracks()

    if not likes or not likes.tracks:
        return "Список любимых композиций пуст."

    track_ids = [
        f"{item.id}:{item.album_id}"
        if item.album_id
        else str(item.id)
        for item in likes.tracks
    ]

    grouped = defaultdict(list)

    for start in range(0, len(track_ids), 100):
        tracks = client.tracks(track_ids[start:start + 100])

        for track in tracks:
            if not track:
                continue

            artists = ", ".join(
                artist.name
                for artist in (track.artists or [])
                if artist.name
            ) or "Неизвестный исполнитель"

            title = track.title or "Без названия"
            version = track.version or ""

            key = (
                artists.casefold(),
                title.casefold(),
                version.casefold(),
            )

            grouped[key].append(track)

    duplicates = {
        key: tracks
        for key, tracks in grouped.items()
        if len(tracks) > 1
    }

    lines = [
        "Проверка повторяющихся композиций",
        f"Дата: {datetime.now():%d.%m.%Y %H:%M}",
        f"Найдено групп совпадений: {len(duplicates)}",
        "",
    ]

    for key, tracks in sorted(duplicates.items()):
        artist, title, version = key

        lines.extend([
            "=" * 55,
            f"Исполнитель: {artist}",
            f"Название: {title}",
            f"Версия: {version or 'Не указана'}",
            f"Количество записей: {len(tracks)}",
            "",
        ])

        for track in tracks:
            lines.extend([
                f"  ID композиции: {track.id}",
                f"  Продолжительность: {track.duration_ms} мс",
            ])

            for album in track.albums or []:
                lines.extend([
                    f"  Альбом: {album.title}",
                    f"  ID альбома: {album.id}",
                    f"  Год: {album.year}",
                    f"  Дата выпуска: {album.release_date}",
                ])

            lines.append("")

    if not duplicates:
        lines.append("Совпадений не обнаружено.")

    return "\n".join(lines)


def inspect_albums(album_ids: list[int]) -> str:
    """Сравнивает расширенные сведения об альбомах."""

    client = connect()

    lines = [
        "Расширенная диагностика альбомов",
        f"Дата: {datetime.now():%d.%m.%Y %H:%M}",
        "",
    ]

    for album_id in album_ids:
        lines.append("=" * 60)
        lines.append(f"Запрошенный ID альбома: {album_id}")

        try:
            album = client.albums_with_tracks(album_id)
        except Exception as error:
            lines.append(f"Ошибка запроса: {error}")
            lines.append("")
            continue

        if album is None:
            lines.append("Альбом не найден.")
            lines.append("")
            continue

        fields = [
            ("Название", "title"),
            ("ID", "id"),
            ("Версия", "version"),
            ("Тип", "type"),
            ("Год", "year"),
            ("Дата выпуска", "release_date"),
            ("Количество композиций", "track_count"),
            ("Количество томов", "volumes"),
            ("Жанр", "genre"),
            ("Метка", "label"),
            ("Правообладатель", "copyright"),
            ("Штрихкод", "barcode"),
            ("Доступность", "available"),
        ]

        for label, attribute in fields:
            value = getattr(album, attribute, None)

            if attribute == "volumes":
                value = len(value) if value else 0

            lines.append(f"{label}: {value}")

        lines.append("")
        lines.append("Состав альбома:")

        for volume_number, volume in enumerate(
            getattr(album, "volumes", None) or [],
            start=1,
        ):
            lines.append(f"  Том {volume_number}:")

            for track in volume:
                artists = ", ".join(
                    artist.name
                    for artist in (track.artists or [])
                    if artist.name
                )

                lines.extend([
                    f"    Название: {track.title}",
                    f"    Исполнители: {artists}",
                    f"    ID: {track.id}",
                    f"    Версия: {track.version}",
                    f"    Продолжительность: {track.duration_ms} мс",
                    "",
                ])

        lines.append("")

    return "\n".join(lines)


def main():
    print("Диагностика Яндекс Музыки")
    print("1 — Проверить композиции по ID")
    print("2 — Найти повторяющиеся композиции")
    print("3 — Сравнить альбомы")

    choice = input("\nВыберите режим: ").strip()

    if choice == "1":
        raw_ids = input(
            "Введите ID композиций через запятую: "
        )

        track_ids = [
            item.strip()
            for item in raw_ids.split(",")
            if item.strip()
        ]

        if not track_ids:
            print("Не указаны идентификаторы композиций.")
            return

        report = inspect_tracks(track_ids)
        report_type = "tracks"

    elif choice == "2":
        report = find_duplicate_tracks()
        report_type = "duplicates"

    elif choice == "3":
        raw_ids = input(
            "Введите ID альбомов через запятую: "
        )

        try:
            album_ids = [
                int(item.strip())
                for item in raw_ids.split(",")
                if item.strip()
            ]
        except ValueError:
            print("Идентификаторы альбомов должны быть числами.")
            return

        if not album_ids:
            print("Не указаны идентификаторы альбомов.")
            return

        report = inspect_albums(album_ids)
        report_type = "albums"

    else:
        print("Неизвестный режим.")
        return

    output_dir = Path(__file__).resolve().parent / "diag"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"{report_type}_{timestamp}.log"

    output.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nОтчёт сохранён: {output.resolve()}")



if __name__ == "__main__":
    main()
