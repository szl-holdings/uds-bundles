"""Offline consumer contract; all archives are synthetic, no release assets used."""
import hashlib
import gzip
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import unittest.mock


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "1234567890abcdef1234567890abcdef12345678"
SPEC = importlib.util.spec_from_file_location("helm_evidence", ROOT / "scripts/helm_evidence.py")
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.consumer = Path(self.temp.name)
        self.script = self.consumer / "helm_evidence.py"
        shutil.copyfile(ROOT / "scripts/helm_evidence.py", self.script)
        shutil.copyfile(ROOT / "LICENSE", self.consumer / "LICENSE")
        self.artifact = self.consumer / "fixture-1.0.0.tgz"
        self.archive([("fixture/Chart.yaml", b"apiVersion: v2\nname: fixture\nversion: 1.0.0\n"),
                      ("fixture/templates/deployment.yaml", b"# synthetic chart\n")])
        self.sha = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.assertEqual(self.run_cli("generate").returncode, 0)

    def archive(self, entries, symlink=False):
        with tarfile.open(self.artifact, "w:gz") as archive:
            for name, contents in entries:
                info = tarfile.TarInfo(name)
                info.size = len(contents)
                if symlink:
                    info.type = tarfile.SYMTYPE
                    info.linkname = "../../outside"
                archive.addfile(info, io.BytesIO(contents))

    def run_cli(self, mode="verify", source=SOURCE, sha=None):
        command = [sys.executable, "-I", str(self.script), mode, self.artifact.name,
                   "--source-sha", source]
        if mode == "verify":
            command += ["--artifact-sha256", self.sha if sha is None else sha]
        return subprocess.run(command, cwd=self.consumer, capture_output=True, text=True, check=False)

    def test_clean_consumer_and_reproducible_evidence(self):
        before = {p.name: p.read_bytes() for p in self.consumer.glob("*.json")}
        self.assertEqual(self.run_cli("generate").returncode, 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.consumer.glob("*.json")})
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unsigned", result.stdout)
        # Consumer contains no checkout, dependencies, git, network client or credentials.
        self.assertFalse((self.consumer / ".git").exists())
        sbom = json.loads(self.artifact.with_suffix(".tgz.cdx.json").read_text())
        self.assertEqual(len(sbom["components"]), 2)
        self.assertEqual(sbom["metadata"]["component"]["licenses"][0]["license"]["id"], "Apache-2.0")

    def test_tampered_artifact(self):
        self.artifact.write_bytes(self.artifact.read_bytes() + b"tampered")
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_missing_evidence(self):
        for suffix in (".cdx.json", ".evidence.json"):
            with self.subTest(suffix=suffix):
                path = self.artifact.with_name(self.artifact.name + suffix)
                original = path.read_bytes()
                path.unlink()
                self.assertNotEqual(self.run_cli().returncode, 0)
                path.write_bytes(original)

    def test_placeholder_and_mismatched_fields(self):
        path = self.artifact.with_name(self.artifact.name + ".evidence.json")
        original = path.read_bytes()
        for field, key, value in [
            ("artifact", "sha256", "PENDING-cosign-attest-at-build"),
            ("artifact", "sha256", "a" * 64),
            ("sbom", "sha256", "b" * 64),
            ("source", "gitCommit", "c" * 40),
            ("source", "repository", "https://example.invalid/other"),
            ("license", "declared", "MIT"),
        ]:
            with self.subTest(field=field, value=value):
                document = json.loads(original)
                document[field][key] = value
                path.write_text(json.dumps(document))
                self.assertNotEqual(self.run_cli().returncode, 0)
        path.write_bytes(original)

    def test_tampered_sbom_and_license(self):
        path = self.artifact.with_name(self.artifact.name + ".cdx.json")
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        self.assertNotEqual(self.run_cli().returncode, 0)
        path.write_bytes(original)
        license_path = self.consumer / "LICENSE"
        license_path.write_bytes(license_path.read_bytes() + b"tampered")
        self.assertNotEqual(self.run_cli().returncode, 0)

    def test_independent_expected_digests_required(self):
        for value in ("", "PENDING", "0" * 64, "d" * 64):
            with self.subTest(value=value):
                self.assertNotEqual(self.run_cli(sha=value).returncode, 0)
        self.assertNotEqual(self.run_cli(source="e" * 40).returncode, 0)
        self.assertNotEqual(self.run_cli("generate", source="PENDING").returncode, 0)

    def test_unsafe_duplicate_and_link_archives(self):
        for name in ("../escape", "/absolute", "fixture/../escape", "fixture\\escape"):
            with self.subTest(name=name):
                self.archive([(name, b"test")])
                self.assertNotEqual(self.run_cli("generate").returncode, 0)
        self.archive([("fixture/Chart.yaml", b"a"), ("fixture/Chart.yaml", b"b")])
        self.assertNotEqual(self.run_cli("generate").returncode, 0)
        self.archive([("fixture/Chart.yaml", b"")], symlink=True)
        self.assertNotEqual(self.run_cli("generate").returncode, 0)

    def test_empty_and_malformed_archives(self):
        self.archive([])
        self.assertNotEqual(self.run_cli("generate").returncode, 0)
        self.artifact.write_bytes(b"not a gzip archive")
        self.assertNotEqual(self.run_cli("generate").returncode, 0)

    def test_total_expansion_bounded_before_metadata_parsing(self):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
            info = tarfile.TarInfo("fixture/Chart.yaml")
            info.pax_headers = {"comment": "x" * 8192}
            archive.addfile(info, io.BytesIO())
        compressed = buffer.getvalue()
        self.assertLess(len(compressed), 2048)
        with unittest.mock.patch.object(EVIDENCE, "MAX_BYTES", 2048):
            with unittest.mock.patch.object(EVIDENCE.tarfile.TarInfo, "frombuf") as parse:
                with self.assertRaisesRegex(ValueError, "total decompressed TAR"):
                    list(EVIDENCE.bounded_members(compressed))
                parse.assert_not_called()
        # Padding and concatenated gzip streams count toward the same total.
        for expanded in (bytes(2049), bytes(1024) + b"x" * 2048):
            with unittest.mock.patch.object(EVIDENCE, "MAX_BYTES", 2048):
                with self.assertRaisesRegex(ValueError, "total decompressed TAR"):
                    list(EVIDENCE.bounded_members(gzip.compress(expanded)))
        with unittest.mock.patch.object(EVIDENCE, "MAX_BYTES", 2048):
            with self.assertRaisesRegex(ValueError, "total decompressed TAR"):
                list(EVIDENCE.bounded_members(gzip.compress(bytes(1024)) + gzip.compress(bytes(1025))))

    def test_extensions_and_nonregular_types_rejected(self):
        for kind in (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME,
                     tarfile.GNUTYPE_LONGLINK, tarfile.GNUTYPE_SPARSE,
                     tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE,
                     tarfile.CHRTYPE, tarfile.BLKTYPE, b"Z"):
            with self.subTest(kind=kind):
                info = tarfile.TarInfo("fixture/metadata")
                info.type = kind
                raw = info.tobuf() + bytes(1024)
                with self.assertRaisesRegex(ValueError, "unsupported TAR type"):
                    list(EVIDENCE.bounded_members(gzip.compress(raw)))

    def test_chart_yaml_must_be_regular_file(self):
        with tarfile.open(self.artifact, "w:gz") as archive:
            directory = tarfile.TarInfo("fixture/Chart.yaml")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            archive.addfile(tarfile.TarInfo("fixture/values.yaml"), io.BytesIO())
        result = self.run_cli("generate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected one nonempty Helm chart", result.stderr)

    def test_file_ancestor_collisions_both_orders(self):
        for names in (("fixture/a", "fixture/a/b"), ("fixture/a/b", "fixture/a")):
            with self.subTest(names=names):
                self.archive([("fixture/Chart.yaml", b"chart")] + [(name, b"file") for name in names])
                result = self.run_cli("generate")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("hierarchy collision", result.stderr)

    def test_directory_roots_and_member_limits(self):
        with tarfile.open(self.artifact, "w:gz") as archive:
            archive.addfile(tarfile.TarInfo("fixture/Chart.yaml"), io.BytesIO())
            directory = tarfile.TarInfo("other")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
        self.assertNotEqual(self.run_cli("generate").returncode, 0)
        with unittest.mock.patch.object(EVIDENCE, "MAX_MEMBERS", 1):
            with self.assertRaisesRegex(ValueError, "too many archive members"):
                list(EVIDENCE.bounded_members(self.artifact.read_bytes()))

    def test_truncation_trailing_data_and_explicit_directories(self):
        raw = tarfile.TarInfo("fixture/Chart.yaml").tobuf()
        for expanded in (raw, raw + bytes(512), raw + bytes(1024) + b"trailing"):
            with self.subTest(size=len(expanded)):
                with self.assertRaises(ValueError):
                    list(EVIDENCE.bounded_members(gzip.compress(expanded)))
        with tarfile.open(self.artifact, "w:gz", format=tarfile.USTAR_FORMAT) as archive:
            directory = tarfile.TarInfo("fixture/")
            directory.type = tarfile.DIRTYPE
            archive.addfile(directory)
            archive.addfile(tarfile.TarInfo("fixture/Chart.yaml"), io.BytesIO())
        self.assertEqual(self.run_cli("generate").returncode, 0)


if __name__ == "__main__":
    unittest.main()
