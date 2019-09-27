
# Quick and dirty test script for TableModel class
# TODO: Improve it and use a proper test class

import os

import emcore as emc
from datavis.views import TableModel


testDataPath = os.environ.get("EM_TEST_DATA", None)

print("hasImpl('star'): ", emc.TableIO.hasImpl('star'))

if testDataPath is not None:
    root = testDataPath + "relion_tutorial/import/"
    fn1 = root + "case1/classify3d_small_it038_data.star";
    print("Reading star: ", fn1)

    t = emc.Table()
    tio = emc.TableIO()
    tio.open(fn1)
    tio.read("images", t)
    tio.close()

    refColNames = [
        "rlnVoltage", "rlnDefocusU", "rlnSphericalAberration",
        "rlnAmplitudeContrast", "rlnImageName", "rlnNormCorrection",
        "rlnMicrographName", "rlnGroupNumber", "rlnOriginX",
        "rlnOriginY", "rlnAngleRot", "rlnAngleTilt", "rlnAnglePsi",
        "rlnClassNumber", "rlnLogLikeliContribution",
        "rlnNrOfSignificantSamples", "rlnMaxValueProbDistribution"
    ]

    tvc1 = TableModel.fromTable(t)
    #print(tvc1)

    colsConfigs = [
        "rlnVoltage",
        "rlnDefocusU",
        "rlnSphericalAberration",
        "rlnAmplitudeContrast",
        ("rlnImageName", {'label': 'ImageName',
                          'renderable': True
                          })
    ]

    tvc2 = TableModel.fromTable(t, colsConfigs)
    print(tvc2)

