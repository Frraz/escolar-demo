def format_bytes(total_bytes: int) -> str:
    if not total_bytes:
        return "0 MB"
    size = float(total_bytes)
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "bytes" else f"{int(size)} bytes"
        size /= 1024
    return f"{size:.1f} TB"
