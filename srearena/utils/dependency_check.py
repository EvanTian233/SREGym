import shutil

def dependency_check(binaries: list[str]):
    for binary in binaries:
        if shutil.which(binary) is None:
            raise RuntimeError(f"[❌] Required dependency '{binary}' not found. Please install {binary}.")