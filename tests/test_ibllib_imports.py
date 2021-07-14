import unittest


class TestIBLRigImports(unittest.TestCase):

    def setUp(self):
        pass

    def test_iblrig_imports(self):
        # List of all import statements in iblrig on dev 20200609
        import ibllib.graphic as graph  # noqa                              .graphic
        import ibllib.io.flags as flags  # noqa                             .flags
        import ibllib.io.params as lib_params  # noqa                     iblutil.io.params
        import ibllib.io.raw_data_loaders as raw  # noqa                    .raw_data_loaders
        import ibllib.pipes.misc as misc  # noqa                            ==
        import oneibl.params  # noqa                                      one.params
        from ibllib.dsp.smooth import rolling_window as smooth  # noqa      ==
        from ibllib.graphic import numinput, popup, strinput  # noqa        .graphic
        from ibllib.io import raw_data_loaders as raw  # noqa               .raw_data_loaders
        from ibllib.misc import logger_config  # noqa                       ==
        from ibllib.pipes.purge_rig_data import purge_local_data  # noqa    .purge_rig_data
        from ibllib.pipes.transfer_rig_data import main  # noqa             .transfer_rig_data
        from oneibl.one import ONE  # noqa                                one.api.ONE
        from oneibl.registration import RegistrationClient  # noqa        one.api.ONE

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main(exit=False)
