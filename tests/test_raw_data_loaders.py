import unittest
import os
import tempfile
from pathlib import Path

import numpy as np

from ibllib.io import flags, jsonable, misc
import iblrig.raw_data_loaders as raw


class TestsRawDataLoaders(unittest.TestCase):

    def setUp(self):
        self.tempfile = tempfile.NamedTemporaryFile(delete=False)
        self.bin_session_path = Path(__file__).parent.joinpath('fixtures', 'sessions',"_iblrig_test_mouse_2020-01-01_001")

    def testFlagFileRead(self):
        # empty file should return True
        self.assertEqual(flags.read_flag_file(self.tempfile.name), True)
        # test with 2 lines and a trailing
        with open(self.tempfile.name, 'w+') as fid:
            fid.write('file1\nfile2\n')
        self.assertEqual(set(flags.read_flag_file(self.tempfile.name)), set(['file1', 'file2']))
        # test with 2 lines and a trailing, Windows convention
        with open(self.tempfile.name, 'w+') as fid:
            fid.write('file1\r\nfile2\r\n')
        self.assertEqual(set(flags.read_flag_file(self.tempfile.name)), set(['file1', 'file2']))

    def testAppendFlagFile(self):
        #  DO NOT CHANGE THE ORDER OF TESTS BELOW
        # prepare a file with 3 dataset types
        file_list = ['_ibl_extraRewards.times', '_ibl_lickPiezo.raw', '_ibl_lickPiezo.timestamps']
        with open(self.tempfile.name, 'w+') as fid:
            fid.write('\n'.join(file_list))
        self.assertEqual(set(flags.read_flag_file(self.tempfile.name)), set(file_list))

        # with an existing file containing files, writing more files append to it
        file_list_2 = ['turltu']
        # also makes sure that if a string is provided it works
        flags.write_flag_file(self.tempfile.name, file_list_2[0])
        self.assertEqual(set(flags.read_flag_file(self.tempfile.name)),
                         set(file_list + file_list_2))

        # writing again keeps unique file values
        flags.write_flag_file(self.tempfile.name, file_list_2[0])
        n = sum([1 for f in flags.read_flag_file(self.tempfile.name) if f == file_list_2[0]])
        self.assertEqual(n, 1)

        # with an existing file containing files, writing empty filelist returns True for all files
        flags.write_flag_file(self.tempfile.name, None)
        self.assertEqual(flags.read_flag_file(self.tempfile.name), True)

        # with an existing empty file, writing filelist returns True for all files
        flags.write_flag_file(self.tempfile.name, ['file1', 'file2'])
        self.assertEqual(flags.read_flag_file(self.tempfile.name), True)

        # makes sure that read after write empty list also returns True
        flags.write_flag_file(self.tempfile.name, [])
        self.assertEqual(flags.read_flag_file(self.tempfile.name), True)

        # with an existing empty file, writing filelist returns the list if clobber
        flags.write_flag_file(self.tempfile.name, ['file1', 'file2', 'file3'], clobber=True)
        self.assertEqual(set(flags.read_flag_file(self.tempfile.name)),
                         set(['file1', 'file2', 'file3']))

        # test the removal of a file within the list
        flags.excise_flag_file(self.tempfile.name, removed_files='file1')
        self.assertEqual(sorted(flags.read_flag_file(self.tempfile.name)), ['file2', 'file3'])

        # if file-list is True it means all files and file_list should be empty after read
        flags.write_flag_file(self.tempfile.name, file_list=True)
        self.assertEqual(flags.read_flag_file(self.tempfile.name), True)

    def test_load_encoder_trial_info(self):
        session = Path(__file__).parent.joinpath('fixtures', 'sessions', 'session_biased_ge5')
        data = raw.load_encoder_trial_info(session)
        self.assertTrue(data is not None)

    def test_load_camera_ssv_times(self):
        session = Path(__file__).parent.joinpath('fixtures', 'sessions', 'session_ephys')
        with self.assertRaises(ValueError):
            raw.load_camera_ssv_times(session, 'tail')
        bonsai, camera = raw.load_camera_ssv_times(session, 'body')
        self.assertTrue(bonsai.size == camera.size == 6001)
        self.assertEqual(bonsai.dtype.str, '<M8[ns]')
        self.assertEqual(str(bonsai[0]), '2020-08-19T16:42:57.790361600')
        expected = np.array([69.466875, 69.5, 69.533, 69.566125, 69.59925])
        np.testing.assert_array_equal(expected, camera[:5])
        # Many sessions have the columns in the wrong order.  Here we write 5 lines from the
        # fixture file to another file in a temporary folder, with the columns swapped.
        from_file = session.joinpath('raw_video_data', '_iblrig_bodyCamera.timestamps.ssv')
        with tempfile.TemporaryDirectory() as tempdir:
            # New file with columns swapped
            to_file = Path(tempdir).joinpath('raw_video_data', '_iblrig_leftCamera.timestamps.ssv')
            to_file.parent.mkdir(exist_ok=True)
            with open(from_file, 'r') as a, open(to_file, 'w') as b:
                for i in range(5):
                    # Read line from fixture file and write into file in swapped order
                    b.write('{1} {0} {2}'.format(*a.readline().split(' ')))
            assert to_file.exists(), 'failed to write test file'
            bonsai, camera = raw.load_camera_ssv_times(to_file.parents[1], 'left')
            # Verify that values returned in the same order as before
            self.assertEqual(bonsai.dtype.str, '<M8[ns]')
            self.assertEqual(camera.dtype.str, '<f8')
            self.assertAlmostEqual(69.466875, camera[0])

    def test_load_camera_gpio(self):
        """
        Embedded frame data comes from 057e25ef-3f80-42e8-aa9f-e259df8bc9ad, left camera
        :return:
        """
        session = Path(__file__).parent.joinpath('fixtures', 'sessions', 'session_ephys')
        gpio = raw.load_camera_gpio(session, 'body', as_dicts=True)
        self.assertEqual(len(gpio), 4)  # One dict per pin
        *gpio_, gpio_4 = gpio  # Check last dict; pin 4 should have one pulse
        self.assertTrue(all(k in ('indices', 'polarities') for k in gpio_4.keys()))
        np.testing.assert_array_equal(gpio_4['indices'], np.array([166, 172], dtype=np.int64))
        np.testing.assert_array_equal(gpio_4['polarities'], np.array([1, -1]))

        # Test raw flag
        gpio = raw.load_camera_gpio(session, 'body', as_dicts=False)
        self.assertEqual(gpio.dtype, bool)
        self.assertEqual(gpio.shape, (510, 4))

        # Test empty / None
        self.assertIsNone(raw.load_camera_gpio(None, 'body'))
        self.assertIsNone(raw.load_camera_gpio(session, 'right'))
        [self.assertIsNone(x) for x in raw.load_camera_gpio(session, 'right', as_dicts=True)]

        # Test noisy GPIO data
        side = 'right'
        with tempfile.TemporaryDirectory() as tdir:
            session_path = Path(tdir).joinpath('mouse', '2020-06-01', '001')
            session_path.joinpath('raw_video_data').mkdir(parents=True)
            filename = session_path / 'raw_video_data' / f'_iblrig_{side}Camera.GPIO.bin'
            np.full(1000, 1.87904819e+09, dtype=np.float64).tofile(filename)
            with self.assertRaises(AssertionError):
                raw.load_camera_gpio(session_path, side, as_dicts=True)

            # Test dead pin array
            np.zeros(3000, dtype=np.float64).tofile(filename)
            with self.assertLogs('ibllib', level='ERROR'):
                gpio = raw.load_camera_gpio(session_path, side, as_dicts=True)
                [self.assertIsNone(x) for x in gpio]

    def test_load_camera_frame_count(self):
        """
        Embedded frame data comes from 057e25ef-3f80-42e8-aa9f-e259df8bc9ad, left camera
        :return:
        """
        session = Path(__file__).parent.joinpath('fixtures', 'sessions', 'session_ephys')
        count = raw.load_camera_frame_count(session, 'body', raw=False)
        np.testing.assert_array_equal(count, np.arange(510, dtype=np.int32))
        self.assertEqual(count.dtype, int)

        # Test raw flag
        count = raw.load_camera_frame_count(session, 'body', raw=True)
        self.assertEqual(count[0], int(16696704))

        # Test empty / None
        self.assertIsNone(raw.load_camera_frame_count(None, 'body'))
        self.assertIsNone(raw.load_camera_frame_count(session, 'right'))

    def test_load_embedded_frame_data(self):
        session = Path(__file__).parent.joinpath('fixtures', 'sessions', 'session_ephys')
        count, gpio = raw.load_embedded_frame_data(session, 'body')
        self.assertEqual(count[0], 0)
        self.assertIsInstance(gpio[-1], dict)
        count, gpio = raw.load_embedded_frame_data(session, 'body', raw=True)
        self.assertNotEqual(count[0], 0)
        self.assertIsInstance(gpio, np.ndarray)

    def test_load_camera_FrameData(self):
        import pandas as pd
        fd_raw = raw.load_camera_frameData(self.bin_session_path, raw=True)
        fd = raw.load_camera_frameData(self.bin_session_path)
        # Wrong camera input file not found
        with self.assertRaises(AssertionError):
            raw.load_camera_frameData(self.bin_session_path, camera='right')
        # Shape
        self.assertTrue(fd.shape[1] == 4)
        self.assertTrue(fd_raw.shape[1] == 4)
        # Type
        self.assertTrue(isinstance(fd, pd.DataFrame))
        self.assertTrue(isinstance(fd_raw, pd.DataFrame))
        # Column names
        df_cols = ["Timestamp", "embeddedTimeStamp",
                   "embeddedFrameCounter", "embeddedGPIOPinState"]
        self.assertTrue(np.all([x in fd.columns for x in df_cols]))
        self.assertTrue(np.all([x in fd_raw.columns for x in df_cols]))
        # Column types
        parsed_dtypes = {
            "Timestamp": np.float64,
            "embeddedTimeStamp": np.float64,
            "embeddedFrameCounter": np.int64,
            "embeddedGPIOPinState": object
        }
        self.assertTrue(fd.dtypes.to_dict() == parsed_dtypes)
        self.assertTrue(all([x == np.int64 for x in fd_raw.dtypes]))

    def tearDown(self):
        self.tempfile.close()
        os.unlink(self.tempfile.name)


class TestsJsonable(unittest.TestCase):

    def testReadWrite(self):
        tfile = tempfile.NamedTemporaryFile(delete=False)
        data = [{'a': 'thisisa', 'b': 1, 'c': [1, 2, 3]},
                {'a': 'thisisb', 'b': 2, 'c': [2, 3, 4]}]
        jsonable.write(tfile.name, data)
        data2 = jsonable.read(tfile.name)
        self.assertEqual(data, data2)
        jsonable.append(tfile.name, data)
        data3 = jsonable.read(tfile.name)
        self.assertEqual(data + data, data3)
        tfile.close()
        os.unlink(tfile.name)


class TestsMisc(unittest.TestCase):

    def setUp(self):
        self._tdir = tempfile.TemporaryDirectory()
        # self.addClassCleanup(tmpdir.cleanup)  # py3.8
        self.tempdir = Path(self._tdir.name)
        self.subdirs = [
            self.tempdir / 'test_empty_parent',
            self.tempdir / 'test_empty_parent' / 'test_empty',
            self.tempdir / 'test_empty',
            self.tempdir / 'test_full',
        ]
        self.file = self.tempdir / 'test_full' / 'file.txt'

        _ = [x.mkdir() for x in self.subdirs]
        self.file.touch()

    def tearDown(self) -> None:
        self._tdir.cleanup()

    def _resetup_folders(self):
        self.file.unlink()
        (self.tempdir / 'test_full').rmdir()
        _ = [x.rmdir() for x in self.subdirs if x.exists()]
        _ = [x.mkdir() for x in self.subdirs]
        self.file.touch()

    def test_delete_empty_folders(self):
        pre = [x.exists() for x in self.subdirs]
        pre_expected = [True, True, True, True]
        self.assertTrue(all([x == y for x, y in zip(pre, pre_expected)]))

        # Test dry run
        pos_expected = None
        pos = misc.delete_empty_folders(self.tempdir)
        self.assertTrue(pos == pos_expected)
        # Test dry=False, non recursive
        pos_expected = [True, False, False, True]
        misc.delete_empty_folders(self.tempdir, dry=False)
        pos = [x.exists() for x in self.subdirs]
        self.assertTrue(all([x == y for x, y in zip(pos, pos_expected)]))

        self._resetup_folders()

        # Test recursive
        pos_expected = [False, False, False, True]
        misc.delete_empty_folders(self.tempdir, dry=False, recursive=True)
        pos = [x.exists() for x in self.subdirs]
        self.assertTrue(all([x == y for x, y in zip(pos, pos_expected)]))


if __name__ == "__main__":
    unittest.main(exit=False, verbosity=2)
