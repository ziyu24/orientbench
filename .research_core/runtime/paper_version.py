from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

import yaml

from . import paper_transactions as transactions
from . import paper_export_transactions as export_transactions


VERSION = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
REVIEW = re.compile(r"v([0-9]{3})\Z")
SOURCE_SUFFIXES = {".tex", ".md"}
PRIMARY_SUFFIXES = SOURCE_SUFFIXES | {".pdf"}
VERSION_MAX_BYTES = 4096
PDF_EXPORT_MAX_BYTES = export_transactions.PDF_MAX_BYTES


def _identity(value: os.stat_result) -> tuple[int, int, int]:
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))


def _file_snapshot(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        *_identity(value),
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _atomic_text(
    path, content, *, expected_parent=None, expected_leaf=None, expected_bytes=None
):
    parent_identity = _require_plain_directory(path.parent, label="paper write parent")
    if expected_parent is not None and parent_identity != expected_parent:
        raise ValueError("paper write parent identity changed")
    if (expected_leaf is None) != (expected_bytes is None):
        raise ValueError("paper write CAS requires leaf identity and bytes")
    if expected_leaf is None:
        _, expected_bytes, expected_leaf = _read_small_plain_payload(
            path.parent, path, label="paper write", parents=(path.parent,)
        )
    if _file_snapshot(_require_plain_file(path, label="paper write")) != expected_leaf:
        raise ValueError(f"paper write CAS changed: {path.name}")
    root = path.parents[2] if path.parent.name == "review" else path.parents[1]
    transactions.begin_version(
        root, path, expected_bytes, content.encode("utf-8"), expected_leaf[:3]
    )
    return _file_snapshot(_require_plain_file(path, label="paper write"))


def _fd_payload(descriptor, limit, *, label):
    os.lseek(descriptor, 0, os.SEEK_SET)
    payload = bytearray()
    while True:
        chunk = os.read(descriptor, limit + 1 - len(payload))
        if not chunk:
            return bytes(payload)
        payload.extend(chunk)
        if len(payload) > limit:
            raise ValueError(f"{label} exceeds {limit} bytes")


def _exclusive_yaml(path, document, *, root, expected_parent=None):
    parent_identity = _require_plain_directory(path.parent, label="paper review directory")
    if expected_parent is not None and parent_identity != expected_parent:
        raise ValueError("paper review directory identity changed")
    payload = yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False
    ).encode("utf-8")
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    parent_descriptor = -1
    created = False
    created_identity: tuple[int, int, int] | None = None
    try:
        if os.name != "nt":
            parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            parent_flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            parent_descriptor = os.open(path.parent, parent_flags)
            if _identity(os.fstat(parent_descriptor)) != parent_identity:
                raise ValueError("paper review directory identity changed")
            descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_descriptor)
        else:
            descriptor = os.open(path, flags, 0o600)
        created = True
        opened = os.fstat(descriptor)
        created_identity = _identity(opened)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("paper review record must be a plain file")
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short paper review write")
            view = view[written:]
        os.fsync(descriptor)
        final = os.fstat(descriptor)
        if _identity(final) != _identity(opened):
            raise ValueError("paper review record identity changed")
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
            descriptor = -1
        try:
            if created and created_identity is not None:
                transactions.quarantine(
                    root, path, expected_identity=created_identity,
                    label="paper review creation compensation",
                    source_dir_fd=parent_descriptor,
                )
        finally:
            if parent_descriptor >= 0:
                os.close(parent_descriptor)
                parent_descriptor = -1
        raise
    return {
        "fd": descriptor,
        "parent_fd": parent_descriptor,
        "identity": created_identity,
        "snapshot": _file_snapshot(final),
        "payload": payload,
        "parent_identity": parent_identity,
        "path": path,
    }


def _root(value: Path) -> Path:
    root = Path(value).resolve(strict=True)
    if not (root / "project.yaml").is_file():
        raise ValueError("paper command requires a project root")
    return root


def _read_small_plain_payload(
    root: Path,
    path: Path,
    *,
    label: str,
    parents: tuple[Path, ...],
) -> tuple[str, bytes, tuple[int, int, int, int, int, int]]:
    _require_contained(root, path, label=label)
    parent_identities = tuple(
        _require_plain_directory(parent, label=f"{label} parent")
        for parent in parents
    )
    before_path = _require_plain_file(path, label=label)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        before_fd = os.fstat(descriptor)
        if _identity(before_fd) != _identity(before_path):
            raise ValueError(f"{label} identity changed before read")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, VERSION_MAX_BYTES + 1 - total)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > VERSION_MAX_BYTES:
                raise ValueError(f"{label} exceeds {VERSION_MAX_BYTES} bytes")
        after_fd = os.fstat(descriptor)
        if _file_snapshot(after_fd) != _file_snapshot(before_fd):
            raise ValueError(f"{label} identity changed during read")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"{label} is missing or unreadable") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    after_path = _require_plain_file(path, label=label)
    if _file_snapshot(after_path) != _file_snapshot(before_path):
        raise ValueError(f"{label} path identity changed or was replaced")
    final_parents = tuple(
        _require_plain_directory(parent, label=f"{label} parent")
        for parent in parents
    )
    if final_parents != parent_identities:
        raise ValueError(f"{label} parent identity changed")
    try:
        payload = b"".join(chunks)
        value = payload.decode("utf-8").strip()
    except UnicodeError as error:
        raise ValueError(f"{label} is not valid UTF-8") from error
    return value, payload, _file_snapshot(after_path)


def _read_small_plain_text(
    root: Path,
    path: Path,
    *,
    label: str,
    parents: tuple[Path, ...],
) -> str:
    return _read_small_plain_payload(
        root, path, label=label, parents=parents
    )[0]


def _read_version(root: Path, paper: Path | None = None) -> str:
    paper = root / "paper" if paper is None else paper
    path = paper / "VERSION"
    value = _read_small_plain_text(
        root, path, label="paper/VERSION", parents=(paper,)
    )
    if VERSION.fullmatch(value) is None:
        raise ValueError("invalid paper version")
    return value


def _next_version(current: str, level: str) -> str:
    match = VERSION.fullmatch(current)
    if match is None or level not in {"major", "minor", "patch"}:
        raise ValueError("invalid paper version bump")
    major, minor, patch = (int(value) for value in match.groups())
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"v{major}.{minor}.{patch}"


def _is_link_like(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if is_junction is not None and is_junction():
            return True
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _require_contained(root: Path, path: Path, *, label: str) -> None:
    try:
        path.absolute().relative_to(root.absolute())
    except ValueError as error:
        raise ValueError(f"{label} escapes the project root") from error


def _require_plain_directory(path: Path, *, label: str) -> tuple[int, int, int]:
    try:
        value = path.stat(follow_symlinks=False)
    except OSError as error:
        raise ValueError(f"{label} is missing or unreadable") from error
    if not stat.S_ISDIR(value.st_mode) or _is_link_like(path):
        raise ValueError(
            f"{label} is missing or is a link, junction, or reparse point"
        )
    return _identity(value)


def _require_plain_file(path: Path, *, label: str) -> os.stat_result:
    try:
        value = path.stat(follow_symlinks=False)
    except OSError as error:
        raise ValueError(f"{label} is missing or unreadable") from error
    if not stat.S_ISREG(value.st_mode) or _is_link_like(path):
        raise ValueError(f"{label} must be a plain file, not a link or reparse point")
    return value


def _verify_exclusive_record(record):
    opened = os.fstat(record["fd"])
    payload = _fd_payload(
        record["fd"], VERSION_MAX_BYTES, label="paper review record"
    )
    after = os.fstat(record["fd"])
    if (
        _identity(opened) != record["identity"]
        or _file_snapshot(opened) != record["snapshot"]
        or _file_snapshot(after) != _file_snapshot(opened)
        or payload != record["payload"]
    ):
        raise ValueError("paper review record identity changed")
    if (
        _require_plain_directory(record["path"].parent, label="paper review directory")
        != record["parent_identity"]
    ):
        raise ValueError("paper review directory identity changed")
    current = _require_plain_file(record["path"], label="paper review record")
    if _identity(current) != record["identity"]:
        raise ValueError("paper review record identity changed")


def _close_exclusive_record(record, *, close_parent=True):
    descriptor = record.get("fd", -1)
    if descriptor >= 0:
        os.close(descriptor)
        record["fd"] = -1
    if close_parent:
        parent_descriptor = record.get("parent_fd", -1)
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
            record["parent_fd"] = -1


def _write_staged_text(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _cleanup_private_staging(
    root: Path, stage: Path, expected_identity: tuple[int, int, int]
) -> None:
    if not os.path.lexists(stage):
        return
    transactions.quarantine(
        root, stage, expected_identity=expected_identity,
        expected_tree=transactions.tree_state(stage),
        label="paper initialization staging compensation",
    )


def _rename_noreplace(source, target):
    return transactions.move_noreplace(source, target)


def _publish_staged_paper(stage: Path, target: Path, root: Path) -> dict:
    stage_identity = _require_plain_directory(
        stage, label="paper initialization staging"
    )
    if os.path.lexists(target):
        raise FileExistsError("paper stage already exists")
    stage_tree = transactions.tree_state(stage)
    published = False
    try:
        _rename_noreplace(stage, target)
        published = True
        if (
            _require_plain_directory(target, label="paper directory")
            != stage_identity
        ):
            raise ValueError("paper publication target identity changed")
        result = _validate_paper_root(root, target)
        if (
            _require_plain_directory(target, label="paper directory")
            != stage_identity
        ):
            raise ValueError("paper publication target identity changed")
        return result
    except BaseException:
        if published:
            transactions.quarantine(
                root, target, expected_identity=stage_identity,
                expected_tree=stage_tree,
                label="paper initialization publication compensation",
            )
        raise


def initialize(root: Path, *, source_format: str = "md") -> dict:
    root = _root(root)
    transactions.recover(root)
    if source_format not in {"md", "tex"}:
        raise ValueError("paper source format must be md or tex")
    paper = root / "paper"
    if os.path.lexists(paper):
        raise FileExistsError("paper stage already exists")
    stage = Path(tempfile.mkdtemp(prefix=".paper-init-", dir=root))
    stage_identity = _require_plain_directory(
        stage, label="paper initialization staging"
    )
    try:
        manuscript = stage / "manuscript"
        review = stage / "review"
        figures = stage / "assets/figures"
        manuscript.mkdir()
        review.mkdir()
        figures.mkdir(parents=True)
        version = "v0.1.0"
        source = manuscript / f"manuscript-{version}.{source_format}"
        _write_staged_text(
            source,
            (
                "# 论文工作稿\n"
                if source_format == "md"
                else "\\documentclass{article}\n\\begin{document}\n论文工作稿\n\\end{document}\n"
            ),
        )
        _write_staged_text(
            stage / "README.md",
            "# 论文\n\n当前版本：`v0.1.0`。主稿：`manuscript/manuscript-v0.1.0."
            + source_format
            + "`。面向用户的说明默认使用中文。\n",
        )
        _write_staged_text(stage / "VERSION", version + "\n")
        _write_staged_text(review / "VERSION", "v001\n")
        _validate_paper_root(root, stage)
        result = _publish_staged_paper(stage, paper, root)
        return {
            "paper_version": result["paper_version"],
            "primary_path": (
                f"paper/manuscript/manuscript-{version}.{source_format}"
            ),
        }
    finally:
        _cleanup_private_staging(root, stage, stage_identity)


def _validate_paper_root(root: Path, paper: Path) -> dict:
    _require_contained(root, paper, label="paper directory")
    paper_identity = _require_plain_directory(paper, label="paper directory")
    version = _read_version(root, paper)
    manuscript = paper / "manuscript"
    manuscript_identity = _require_plain_directory(
        manuscript, label="paper manuscript directory"
    )
    assets = paper / "assets"
    _require_plain_directory(assets, label="paper figures parent")
    figures = assets / "figures"
    _require_plain_directory(figures, label="paper figures directory")
    review = paper / "review"
    _require_plain_directory(review, label="paper review directory")
    source_files: list[Path] = []
    primary_files: list[Path] = []
    names = sorted(path.name for path in manuscript.iterdir())
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("paper manuscript contains duplicate case-folded entries")
    allowed = {
        *(f"manuscript-{version}{suffix}" for suffix in SOURCE_SUFFIXES),
        f"manuscript-{version}.pdf",
    }
    for name in names:
        path = manuscript / name
        if name not in allowed:
            if name.casefold().startswith("manuscript-") and (
                path.suffix.casefold() in PRIMARY_SUFFIXES
            ):
                raise ValueError("paper primary file requires a versioned filename")
            raise ValueError(f"paper manuscript closed set has unexpected entry: {name}")
        _require_plain_file(path, label=f"paper manuscript entry {name}")
        primary_files.append(path)
        if path.suffix in SOURCE_SUFFIXES:
            source_files.append(path)
    if len(source_files) != 1:
        raise ValueError("paper requires exactly one versioned source manuscript")
    pdfs = [path for path in primary_files if path.suffix == ".pdf"]
    if len(pdfs) > 1:
        raise ValueError("paper permits at most one current-version PDF")
    if pdfs:
        export_transactions.require_explicit_pdf(
            root, version, pdfs[0].relative_to(root).as_posix(), manuscript_identity
        )
    if _require_plain_directory(
        manuscript, label="paper manuscript directory"
    ) != manuscript_identity:
        raise ValueError("paper manuscript directory identity changed")
    review_version = _read_small_plain_text(
        root,
        review / "VERSION",
        label="paper/review/VERSION",
        parents=(paper, review),
    )
    if REVIEW.fullmatch(review_version) is None:
        raise ValueError("invalid paper review version")
    if _require_plain_directory(paper, label="paper directory") != paper_identity:
        raise ValueError("paper directory identity changed")
    return {
        "paper_version": version,
        "review_version": review_version,
        "primary_files": [path.relative_to(root).as_posix() for path in primary_files],
    }


def validate(root: Path) -> dict:
    root = _root(root)
    transactions.recover(root)
    return _validate_paper_root(root, root / "paper")


def _export_file_state(root, path, *, label, parents):
    _require_contained(root, path, label=label)
    parent_state = tuple(
        _require_plain_directory(parent, label=f"{label} parent")
        for parent in parents
    )
    before = _file_snapshot(_require_plain_file(path, label=label))
    payload = transactions.read_file(path, PDF_EXPORT_MAX_BYTES)
    after = _file_snapshot(_require_plain_file(path, label=label))
    final_parents = tuple(
        _require_plain_directory(parent, label=f"{label} parent")
        for parent in parents
    )
    if after != before or final_parents != parent_state:
        raise ValueError(f"{label} changed during PDF export")
    return payload, before, parent_state


def _verify_export_file(root, path, expected, *, label, parents):
    try:
        current = _export_file_state(root, path, label=label, parents=parents)
    except (OSError, ValueError) as error:
        raise ValueError(f"{label} changed during PDF export") from error
    if current != expected:
        raise ValueError(f"{label} changed during PDF export")


def export_pdf(root: Path, *, runner=subprocess.run) -> dict:
    root = _root(root)
    export_transactions.recover(root)
    paper_root = root / "paper"
    manuscript = paper_root / "manuscript"
    version = _read_version(root, paper_root)
    _require_plain_directory(manuscript, label="paper manuscript directory")
    target = manuscript / f"manuscript-{version}.pdf"
    if os.path.lexists(target):
        _require_plain_file(target, label="existing versioned PDF")
        raise FileExistsError("versioned PDF already exists")
    paper = validate(root)
    version = paper["paper_version"]
    primary = [root / relative for relative in paper["primary_files"]]
    sources = [path for path in primary if path.suffix in SOURCE_SUFFIXES]
    if len(sources) != 1:
        raise ValueError("paper requires exactly one current source manuscript")
    source = sources[0]
    if source.suffix.casefold() != ".md":
        raise ValueError("explicit PDF export currently requires Markdown source")
    target = manuscript / f"manuscript-{version}.pdf"
    if os.path.lexists(target):
        raise FileExistsError("versioned PDF already exists")

    watched = (
        (
            source,
            "paper source",
            (paper_root, manuscript),
        ),
        (paper_root / "VERSION", "paper/VERSION", (paper_root,)),
        (paper_root / "README.md", "paper README", (paper_root,)),
    )
    input_states = {
        path: _export_file_state(root, path, label=label, parents=parents)
        for path, label, parents in watched
    }
    manuscript_identity = _require_plain_directory(
        manuscript, label="paper manuscript directory"
    )
    tx = export_transactions.begin(root, version)
    temporary = None
    published = False
    try:
        with export_transactions.parent_guard(tx) as runner_guard:
            temporary = export_transactions.create_temp(tx, guard=runner_guard)
            generation = export_transactions.parent_generation(runner_guard)
            arguments = [
                "pandoc",
                source.relative_to(root).as_posix(),
                "--to=pdf",
                "--output",
                export_transactions.runner_output_path(
                    runner_guard, temporary.name
                ),
            ]
            runner_error = None
            try:
                runner_kwargs = {
                    "cwd": root,
                    "shell": False,
                    "check": False,
                    "capture_output": True,
                }
                runner_kwargs.update(
                    export_transactions.runner_options(runner_guard)
                )
                completed = runner(
                    arguments,
                    **runner_kwargs,
                )
            except FileNotFoundError as error:
                runner_error = ValueError("pandoc executable was not found")
                runner_error.__cause__ = error
                completed = None
            except Exception as error:
                runner_error = ValueError("PDF export runner failed")
                runner_error.__cause__ = error
                completed = None

            export_transactions.check_parent_generation(runner_guard, generation)
            for path, label, parents in watched:
                _verify_export_file(
                    root, path, input_states[path], label=label, parents=parents
                )
            if runner_error is not None:
                raise runner_error
            if getattr(completed, "returncode", None) != 0:
                raise ValueError("pandoc PDF export failed")
            pdf_payload = export_transactions.read_output(tx, runner_guard)
            if not pdf_payload.startswith(b"%PDF-"):
                raise ValueError("PDF export output has an invalid PDF signature")
            for path, label, parents in watched:
                _verify_export_file(
                    root, path, input_states[path], label=label, parents=parents
                )
            export_transactions.bind_output(tx, pdf_payload, guard=runner_guard)
        target = export_transactions.publish(tx)
        published = True
        if (
            _require_plain_directory(manuscript, label="paper manuscript directory")
            != manuscript_identity
            or transactions.read_file(target, PDF_EXPORT_MAX_BYTES) != pdf_payload
        ):
            raise ValueError("published PDF changed during verification")
        for path, label, parents in watched:
            _verify_export_file(
                root, path, input_states[path], label=label, parents=parents
            )
        return {
            "paper_version": version,
            "pdf_path": target.relative_to(root).as_posix(),
            "source_path": source.relative_to(root).as_posix(),
        }
    except BaseException:
        if published:
            export_transactions.retract(tx)
        else:
            if (
                temporary is not None
                and tx.get("expected_file") is None
                and os.path.lexists(temporary)
            ):
                try:
                    partial = transactions.read_file(
                        temporary, PDF_EXPORT_MAX_BYTES
                    )
                    export_transactions.bind_output(tx, partial)
                except (OSError, ValueError):
                    pass
            export_transactions.abort(tx)
        raise


def bump(root: Path, *, level: str) -> dict:
    root = _root(root)
    paper = validate(root)
    current = paper["paper_version"]
    target_version = _next_version(current, level)
    primary = [root / relative for relative in paper["primary_files"]]
    if any(path.suffix == ".pdf" for path in primary):
        raise ValueError("paper bump refuses an existing current-version PDF")
    sources = [path for path in primary if path.suffix in SOURCE_SUFFIXES]
    if len(sources) != 1:
        raise ValueError("paper requires exactly one current source manuscript")
    source = sources[0]
    target = source.with_name(f"manuscript-{target_version}{source.suffix}")
    if os.path.lexists(target):
        raise FileExistsError(f"paper version target already exists: {target.name}")
    paper_root = root / "paper"
    version_path = paper_root / "VERSION"
    version_value, version_bytes, _ = _read_small_plain_payload(
        root,
        version_path,
        label="paper/VERSION",
        parents=(paper_root,),
    )
    if version_value != current:
        raise ValueError("paper VERSION changed after validation")
    readme_path = root / "paper/README.md"
    old_readme = transactions.read_file(readme_path)
    try:
        new_readme = old_readme.decode("utf-8").replace(
            current, target_version
        ).encode("utf-8")
    except UnicodeError as error:
        raise ValueError("paper README is not valid UTF-8") from error
    transactions.read_file(source)
    transactions.begin_bump(
        root, source, target, version_path, version_bytes,
        (target_version + "\n").encode("utf-8"),
        readme_path, old_readme, new_readme,
    )
    return validate(root)


def record_review(root: Path, *, summary: str) -> Path:
    root = _root(root)
    transactions.recover(root)
    if type(summary) is not str or not summary.strip() or len(summary) > 240:
        raise ValueError("review summary must be concise")
    paper = validate(root)
    review_root = root / "paper/review"
    review_identity = _require_plain_directory(
        review_root, label="paper review directory"
    )
    version_path = review_root / "VERSION"
    review_version, review_version_bytes, review_version_leaf = (
        _read_small_plain_payload(
            root,
            version_path,
            label="paper/review/VERSION",
            parents=(root / "paper", review_root),
        )
    )
    if review_version != paper["review_version"]:
        raise ValueError("paper review VERSION changed after validation")
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    ).stdout
    if status.strip():
        raise ValueError("paper review requires a clean worktree")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    ).stdout.strip()
    current = paper["review_version"]
    path = review_root / f"review-{current}.yaml"
    if os.path.lexists(path):
        _require_plain_file(path, label="existing paper review record")
        number = int(REVIEW.fullmatch(current).group(1)) + 1
        if number > 999:
            raise ValueError("paper review version exhausted")
        current = f"v{number:03d}"
        path = review_root / f"review-{current}.yaml"
    document = {
        "schema_version": 1,
        "review_version": current,
        "paper_version": paper["paper_version"],
        "paper_git_sha": head,
        "summary": summary.strip(),
    }
    record = _exclusive_yaml(
        path, document, root=root, expected_parent=review_identity
    )
    version_written = False
    written_version_leaf: tuple[int, int, int, int, int, int] | None = None
    try:
        _verify_exclusive_record(record)
        written_version_leaf = _atomic_text(
            version_path,
            current + "\n",
            expected_parent=review_identity,
            expected_leaf=review_version_leaf,
            expected_bytes=review_version_bytes,
        )
        version_written = True
        _verify_exclusive_record(record)
        if _read_small_plain_text(
            root,
            version_path,
            label="paper/review/VERSION",
            parents=(root / "paper", review_root),
        ) != current:
            raise ValueError("paper review version update failed")
        _verify_exclusive_record(record)
    except BaseException as error:
        compensation_error: BaseException | None = None
        try:
            if version_written and written_version_leaf is not None:
                _atomic_text(
                    version_path,
                    review_version_bytes.decode("utf-8"),
                    expected_parent=review_identity,
                    expected_leaf=written_version_leaf,
                    expected_bytes=(current + "\n").encode("utf-8"),
                )
        except (OSError, UnicodeError, ValueError, RuntimeError) as caught:
            compensation_error = caught
        try:
            _close_exclusive_record(record, close_parent=False)
        except OSError as caught:
            if compensation_error is None:
                compensation_error = caught
        try:
            transactions.quarantine(
                root, path, expected_identity=record["identity"],
                expected_payload=record["payload"],
                label="paper review record compensation",
                source_dir_fd=record["parent_fd"],
            )
        except (OSError, ValueError, RuntimeError) as caught:
            if compensation_error is None:
                compensation_error = caught
        if compensation_error is not None:
            raise RuntimeError("paper review compensation requires audit") from compensation_error
        raise error
    finally:
        _close_exclusive_record(record)
    return path
