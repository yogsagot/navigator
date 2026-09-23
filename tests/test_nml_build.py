"""Building a directory of documents, and checking one that was built.

``navml/build.py`` and ``navml/__main__.py``.  Everything is done in a throwaway
package under ``tmp_path``, except the last test, which is the standing
regression: the components this repository ships must stay in step with their
markup.
"""

from __future__ import annotations

import sys

import pytest

from navml.build import build, discover, order, package_of
from navml.errors import MarkupError
from navml.generator import MARKER
from navml.__main__ import BROKEN, OK, STALE, main


@pytest.fixture
def package(tmp_path, monkeypatch):
    """A throwaway component package on ``sys.path``, deliberately **flat**.

    The repository puts each component in a directory of its own, but the flat
    shape -- a component's modules sitting straight in the package -- is still
    legal, and this fixture is the only thing left that exercises it.  Keep it
    flat; the nested one below is a separate fixture for that reason.
    """
    name = "pkg_" + tmp_path.name.replace("-", "_")
    directory = tmp_path / name
    directory.mkdir()
    (directory / "__init__.py").write_text("import navml\nnavml.register(__name__)\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    yield directory
    for module in [m for m in sys.modules if m.startswith(name)]:
        del sys.modules[module]


def write(package, stem: str, markup: str, handwritten: str | None = None):
    (package / f"{stem}.nml").write_text(markup, encoding="utf-8")
    if handwritten is not None:
        (package / f"{stem}.py").write_text(handwritten, encoding="utf-8")


# -- finding and ordering ----------------------------------------------------


def test_a_directory_is_searched_for_documents(package):
    write(package, "one", "One:\n")
    write(package, "two", "Two:\n")
    assert [p.name for p in discover([package])] == ["one.nml", "two.nml"]


def test_the_package_is_read_off_the_directories(package):
    write(package, "one", "One:\n")
    assert package_of(package / "one.nml") == package.name


def test_a_document_is_built_after_the_ones_it_imports(package):
    write(package, "outer", f"from {package.name}.inner import Inner\n\nOuter:\n")
    write(package, "inner", "Inner:\n")
    assert [p.stem for p in order(discover([package]))] == ["inner", "outer"]


def test_two_documents_importing_each_other_are_an_error(package):
    write(package, "a", f"from {package.name}.b import B\n\nA:\n")
    write(package, "b", f"from {package.name}.a import A\n\nB:\n")
    with pytest.raises(MarkupError) as caught:
        order(discover([package]))
    assert "import each other" in caught.value.message


# -- a cold build ------------------------------------------------------------


def test_a_cold_build_writes_both_artefacts(package):
    write(package, "one", "One:\n    property text: \"\"\n")
    report = build([package])
    assert sorted(p.name for p in report.written) == ["one.pyi", "one_nml.py"]
    assert (package / "one_nml.py").read_text().startswith(MARKER)


def test_a_cold_build_compiles_a_document_against_one_it_just_wrote(package):
    """Which is the whole reason the order exists."""
    write(package, "inner", "Inner:\n    property text: \"\"\n")
    write(
        package,
        "outer",
        f"from {package.name}.inner import Inner\n\n"
        "Outer:\n    property caption: \"hi\"\n\n"
        "    Inner:\n        id: a\n        text: parent.caption\n",
    )
    build([package])
    module = __import__(f"{package.name}.outer", fromlist=["Outer"])
    assert module.Outer().a.text == "hi"


def test_building_twice_writes_nothing_the_second_time(package):
    write(package, "one", "One:\n")
    build([package])
    report = build([package])
    assert report.written == []
    assert len(report.unchanged) == 2


# -- checking ----------------------------------------------------------------


def test_check_is_clean_after_a_build(package):
    write(package, "one", "One:\n")
    build([package])
    report = build([package], check_only=True)
    assert report.ok and report.stale == []


def test_check_reports_the_first_differing_line_and_writes_nothing(package):
    write(package, "one", "One:\n    property text: \"\"\n")
    build([package])
    before = (package / "one_nml.py").read_text()
    write(package, "one", "One:\n    property text: \"changed\"\n")
    report = build([package], check_only=True)
    assert not report.ok
    assert report.stale[0].differs
    assert (package / "one_nml.py").read_text() == before


def test_check_reports_a_document_that_was_never_built(package):
    write(package, "one", "One:\n")
    assert not build([package], check_only=True).ok


# -- what it refuses ---------------------------------------------------------


def test_a_file_navml_did_not_write_is_not_overwritten(package):
    write(package, "one", "One:\n")
    (package / "one_nml.py").write_text("# mine\n")
    with pytest.raises(MarkupError) as caught:
        build([package])
    assert "was not written by navml" in caught.value.message


def test_an_interrupted_build_leaves_nothing_behind(package):
    write(package, "one", "One:\n")
    build([package])
    assert not list(package.glob("*.navml-new"))


# -- the command -------------------------------------------------------------


def test_the_command_builds_and_then_checks_clean(package, capsys):
    write(package, "one", "One:\n")
    assert main(["build", str(package)]) == OK
    assert main(["build", str(package), "--check"]) == STALE - 1


def test_the_command_reports_drift(package, capsys):
    write(package, "one", "One:\n")
    assert main(["build", str(package), "--check"]) == STALE
    assert "stale" in capsys.readouterr().err


def test_the_command_reports_a_broken_document_in_one_line(package, capsys):
    write(package, "one", "One:\n    Missing:\n        id: a\n")
    assert main(["build", str(package)]) == BROKEN
    error = capsys.readouterr().err
    assert error.count("\n") == 1
    assert "one.nml:2" in error


# -- a component is a directory ----------------------------------------------


@pytest.fixture
def nested(tmp_path, monkeypatch):
    """A throwaway component package whose components are directories.

    The shape the repository itself uses: ``pkg/one/one.nml`` beside
    ``pkg/one/__init__.py``, so the document compiles to ``pkg.one.one`` while
    everything that wants it writes ``from pkg.one import One``.
    """
    name = "nest_" + tmp_path.name.replace("-", "_")
    directory = tmp_path / name
    directory.mkdir()
    (directory / "__init__.py").write_text("import navml\nnavml.register(__name__)\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    yield directory
    for module in [m for m in sys.modules if m.startswith(name)]:
        del sys.modules[module]


def write_nested(package, stem: str, name: str, markup: str, handwritten=None):
    """One component, in a directory of its own that re-exports *name*."""
    component = package / stem
    component.mkdir(exist_ok=True)
    (component / "__init__.py").write_text(
        f"from {package.name}.{stem}.{stem} import {name}\n"
        f'__all__ = ["{name}"]\n',
        encoding="utf-8",
    )
    (component / f"{stem}.nml").write_text(markup, encoding="utf-8")
    if handwritten is not None:
        (component / f"{stem}.py").write_text(handwritten, encoding="utf-8")
    return component


def test_a_component_directory_is_ordered_by_the_name_it_is_imported_by(nested):
    """The public name, which is the directory -- not the module inside it.

    A document writes ``from pkg.base import Base``; the document it names
    compiles to ``pkg.base.base``.  Keying the graph on only the second makes
    every edge vanish, and the order falls back on the alphabet with no error
    -- so the names here are chosen to make the alphabet the *wrong* answer.
    """
    write_nested(nested, "base", "Base", "Base:\n")
    write_nested(
        nested, "apex", "Apex",
        f"from {nested.name}.base import Base\n\nApex:\n",
    )
    assert [p.stem for p in order(discover([nested]))] == ["base", "apex"]


def test_a_cold_build_of_nested_components_compiles_in_order(nested):
    """The same proof as the flat one, one package deeper.

    ``apex`` sorts first and must be built second, so this fails outright
    rather than by luck if the ordering regresses.
    """
    write_nested(nested, "base", "Base", "Base:\n    property text: \"\"\n")
    write_nested(
        nested,
        "apex",
        "Apex",
        f"from {nested.name}.base import Base\n\n"
        "Apex:\n    property caption: \"hi\"\n\n"
        "    Base:\n        id: a\n        text: parent.caption\n",
    )
    build([nested])
    module = __import__(f"{nested.name}.apex", fromlist=["Apex"])
    assert module.Apex().a.text == "hi"


def test_a_rebuild_replaces_the_class_the_component_package_re_exports(nested):
    """``_forget`` has to drop the *package*, not only the module.

    A component directory's ``__init__`` binds the class, so leaving that
    package in ``sys.modules`` after a write means the next document resolves
    ``from pkg.inner import Inner`` against the class from before the build --
    and gets no error, just the old one.
    """
    write_nested(nested, "inner", "Inner", "Inner:\n    property text: \"\"\n")
    build([nested])
    before = __import__(f"{nested.name}.inner", fromlist=["Inner"]).Inner
    assert "later" not in dict(vars(before))

    write_nested(nested, "inner", "Inner", "Inner:\n    property text: \"\"\n    property later: 1\n")
    build([nested])
    after = __import__(f"{nested.name}.inner", fromlist=["Inner"]).Inner
    assert after is not before
    assert after().later == 1


@pytest.mark.parametrize("tree", ["navml/widgets", "navigator/widgets"])
def test_every_component_directory_is_a_package(tree):
    """Without an ``__init__.py`` the failure is silent in both directions.

    ``package_of`` walks up *while* one is there, so it answers ``None``
    instead of the library's name; and the directory still imports, as a
    namespace package, so the symptom is a bare ``AttributeError`` from the
    library's lazy re-export with nothing pointing here.
    """
    import pathlib

    for directory in sorted(pathlib.Path(tree).iterdir()):
        if not directory.is_dir() or directory.name == "__pycache__":
            continue
        assert (directory / "__init__.py").exists(), f"{directory} is not a package"
        assert package_of(directory / "x.nml") == tree.replace("/", ".") + f".{directory.name}"


# -- the components this repository ships ------------------------------------


@pytest.mark.parametrize("tree", ["navml/widgets", "navigator/widgets"])
def test_the_shipped_components_are_in_step_with_their_markup(tree):
    """The regression that keeps both component packages honest.

    Two directories rather than one: the application's screens are a component
    package too, and a `--check' that named only navml's would pass while
    `manager.nml' drifted.
    """
    report = build([tree], check_only=True)
    assert report.ok, [
        f"{a.path.name}:{a.differs}" for a in report.stale
    ]
