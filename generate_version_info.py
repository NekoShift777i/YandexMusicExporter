
"""Создание сведений о версии для исполняемого файла Windows."""

from pathlib import Path

from app_info import (
    APP_AUTHOR,
    APP_COPYRIGHT,
    APP_DESCRIPTION,
    APP_EXECUTABLE,
    APP_NAME,
    APP_VERSION,
)


def generate_version_info():
    version_parts = [int(part) for part in APP_VERSION.split(".")]

    while len(version_parts) < 4:
        version_parts.append(0)

    version_tuple = tuple(version_parts[:4])
    version_string = ".".join(map(str, version_tuple))

    fields = {
        "CompanyName": APP_AUTHOR,
        "FileDescription": APP_DESCRIPTION,
        "FileVersion": version_string,
        "InternalName": APP_EXECUTABLE,
        "LegalCopyright": APP_COPYRIGHT,
        "OriginalFilename": f"{APP_EXECUTABLE}.exe",
        "ProductName": APP_NAME,
        "ProductVersion": APP_VERSION,
    }

    string_fields = ",\n".join(
        f"StringStruct({key!r}, {value!r})"
        for key, value in fields.items()
    )

    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple!r},
    prodvers={version_tuple!r},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          {string_fields}
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

    output = Path(__file__).resolve().parent / "version_info.txt"
    output.write_text(content, encoding="utf-8")

    print(f"Сведения о версии созданы: {output}")


if __name__ == "__main__":
    generate_version_info()
