import json
import unittest

import plotter
import test_server as fixtures

manager = fixtures.manager
HEADERS = {"Content-Type": "application/json", "X-Manager-Plotter": "1"}
SOURCE = b"IN;VS32,1;PW0.350,1;WU0;SP5;PU-20 -60;PD80 -60;PA80,-20,-20,-60;LT;PU30 -40;PR;PD0,20;SP0;"


class PlotterTests(unittest.TestCase):
    setUp = fixtures.ManagerTests.setUp
    tearDown = fixtures.ManagerTests.tearDown
    folder = fixtures.ManagerTests.folder
    file = fixtures.ManagerTests.file
    http = fixtures.ManagerTests.http
    url = fixtures.ManagerTests.url

    def test_rotation_origin_axis_scale_and_lift_between_contours(self):
        self.assertEqual(plotter.convert(SOURCE, 95, 80),
                         b"IN;;\r\nPU0 80;\r\nPD0 0;\r\nPD38 0;\r\nPD0 80;\r\n"
                         b"PU19 40;\r\nPD38 40;\r\nPU0 0;\r\nPU;\r\n")
        for bad in (b"IN;SC0,100,0,100;PD10 10;", b"IN;PU8 8;PD12;", b"IN;PU2 2;",
                    b"IN;PU10 10;PD20 20;VS32\nPU30 30;PD40 40;"):
            with self.assertRaises(ValueError):
                plotter.convert(bad, 100, 100)

    def test_file_listing_and_conversion_in_cutter_only(self):
        for folder in ("Клиент/2026-00-00 - Заказ/#  CUTTER", "# work/# cutter"):
            source = folder + "/Цветок.PLT"
            self.file(source, SOURCE)
            self.file(folder + "/Примечание.txt", b"ok")
            legacy = folder + "/Цветок - e-cut.plt"
            self.file(legacy, b"working file")
            _, _, data = self.http(self.url("/api/folder", folder))
            files = {file["name"]: file for file in json.loads(data)["files"]}
            self.assertEqual(files["Цветок.PLT"]["plotterAction"], "convert")
            self.assertEqual(files["Цветок - e-cut.plt"]["plotterAction"], "download")
            if folder.startswith("# work"):
                self.assertNotIn("Примечание.txt", files)
            request = dict(path=source, source_key=files["Цветок.PLT"]["plotterSourceKey"])
            status, _, result = self.http("/api/plotter-convert", "POST", json.dumps(request), HEADERS)
            self.assertEqual(status, 201, result)
            first = json.loads(result)
            self.assertEqual(first["name"], "Цветок-gpt.plt")
            _, _, data = self.http(self.url("/api/folder", folder))
            files = {file["name"]: file for file in json.loads(data)["files"]}
            self.assertEqual(files[first["name"]]["plotterAction"], "download")
            status, _, result = self.http("/api/plotter-convert", "POST", json.dumps(request), HEADERS)
            self.assertEqual(status, 201, result)
            saved = json.loads(result)
            self.assertEqual(saved["name"], "Цветок-2-gpt.plt")
            expected = plotter.convert(SOURCE, 98.6174, 98.6174)
            self.assertEqual((self.root / first["path"]).read_bytes(), expected)
            self.assertEqual((self.root / saved["path"]).read_bytes(), expected)
            self.assertEqual((self.root / source).read_bytes(), SOURCE)
            self.assertEqual((self.root / legacy).read_bytes(), b"working file")
            self.file(source, SOURCE + b"\r\n")
            self.assertEqual(self.http("/api/plotter-convert", "POST", json.dumps(request), HEADERS)[0], 409)
            self.assertEqual(self.http("/api/plotter-convert", "POST", json.dumps(dict(path=saved["path"])), HEADERS)[0], 400)
        self.assertEqual(self.http("/api/plotter-convert", "POST", json.dumps({"path": "# docs/test.plt"}), HEADERS)[0], 400)

    def test_settings_are_validated_versioned_and_audited(self):
        _, _, data = self.http("/api/plotter-settings")
        original = json.loads(data)
        self.assertEqual(original, {"revision": "missing", "x_percent": 98.6174, "y_percent": 98.6174})
        payload = dict(original, x_percent="97,45", y_percent="100.2")
        self.assertEqual(self.http("/api/plotter-settings", "POST", json.dumps(payload), {"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.http("/api/plotter-settings", "POST", json.dumps(dict(payload, y_percent="0")), HEADERS)[0], 400)
        status, _, data = self.http("/api/plotter-settings", "POST", json.dumps(payload), HEADERS)
        self.assertEqual(status, 200)
        saved = json.loads(data)
        self.assertEqual((saved["x_percent"], saved["y_percent"]), (97.45, 100.2))
        self.assertEqual(self.http("/api/plotter-settings", "POST", json.dumps(payload), HEADERS)[0], 409)
        plotter.settings(manager.order_store(), dict(saved, x_percent="100"))
        with manager.order_store().connect() as db:
            data = db.execute("SELECT data FROM metadata_history WHERE entity='metadata_records'").fetchone()[0]
            self.assertEqual(json.loads(json.loads(data)["data"])["x_percent"], 97.45)
